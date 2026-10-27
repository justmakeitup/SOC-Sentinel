"""Ingestion pipeline service orchestrating parsing, validation, and storage."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.normalizer import EventNormalizer
from app.ingestion.parsers import (
    AuthLogParser,
    BaseLogParser,
    FirewallLogParser,
    GenericLogParser,
)
from app.ingestion.parsers.base import RejectedRecord
from app.ingestion.schemas import IngestionUploadResponse, RejectedRecordItem
from app.models.event import NormalizedSecurityEvent
from app.models.log_source import (
    IngestionJob,
    IngestionJobStatus,
    LogSource,
    LogSourceStatus,
    LogSourceType,
)


class IngestionService:
    """Enterprise ingestion coordinator ensuring secure, idempotent log processing."""

    def __init__(self, db: Session):
        self.db = db
        self.normalizer = EventNormalizer()

    def select_parser(
        self,
        parser_type: str,
        content_sample: str,
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> BaseLogParser:
        """Resolves the appropriate parser based on user hint or content analysis."""
        norm_type = parser_type.lower().strip()
        if norm_type == "auth":
            return AuthLogParser()
        if norm_type in ("firewall", "network", "nids"):
            return FirewallLogParser()
        if norm_type in ("generic", "generic_json", "csv"):
            return GenericLogParser(field_mapping=field_mapping)

        # Automatic detection heuristic
        sample_lower = content_sample[:1024].lower()
        if any(term in sample_lower for term in ("login", "auth_method", "user_name", "password", "logon")):
            return AuthLogParser()
        if any(term in sample_lower for term in ("src_port", "dst_port", "protocol", "drop", "allow", "packets")):
            return FirewallLogParser()

        return GenericLogParser(field_mapping=field_mapping)

    def get_or_create_default_source(
        self,
        source_id: Optional[UUID],
        detected_type: LogSourceType = LogSourceType.CUSTOM,
    ) -> LogSource:
        """Retrieves designated log source or provisions an ingestion feed collector."""
        if source_id:
            src = self.db.query(LogSource).filter(LogSource.id == source_id).first()
            if not src:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"LogSource with ID '{source_id}' does not exist.",
                )
            return src

        # Look for default collector
        default_name = "Direct-Upload-Collector"
        src = self.db.query(LogSource).filter(LogSource.name == default_name).first()
        if not src:
            src = LogSource(
                name=default_name,
                source_type=detected_type,
                description="Default ingestion feed for analyst manual imports",
                status=LogSourceStatus.ACTIVE,
                retention_days=90,
            )
            self.db.add(src)
            self.db.commit()
            self.db.refresh(src)
        return src

    def process_file_import(
        self,
        filename: str,
        content_bytes: bytes,
        source_id: Optional[UUID] = None,
        parser_type: str = "auto",
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> IngestionUploadResponse:
        """Processes an uploaded telemetry file securely from buffer to database."""
        # 1. Enforce upload size limit
        byte_length = len(content_bytes)
        if byte_length > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum upload size limit of {max_mb} MB.",
            )

        if byte_length == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # 2. Enforce file extension check
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            allowed_str = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Accepted formats: {allowed_str}",
            )

        # 3. Decode safely without executing content
        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content_bytes.decode("utf-8-sig")  # Excel BOM
            except UnicodeDecodeError:
                try:
                    content_str = content_bytes.decode("latin-1")
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File content could not be decoded as text/JSON.",
                    )

        # 4. Compute batch identifier for idempotency tracking
        batch_identifier = hashlib.sha256(content_bytes).hexdigest()

        # Check if identical batch was already processed
        existing_job = (
            self.db.query(IngestionJob)
            .filter(
                IngestionJob.batch_identifier == batch_identifier,
                IngestionJob.status.in_([IngestionJobStatus.COMPLETED, IngestionJobStatus.PARTIALLY_FAILED]),
            )
            .first()
        )
        if existing_job:
            # Idempotent response: report duplicate batch
            source = self.db.query(LogSource).filter(LogSource.id == existing_job.log_source_id).first()
            source_name = source.name if source else "Unknown"
            return IngestionUploadResponse(
                job_id=existing_job.id,
                status=existing_job.status,
                source_id=existing_job.log_source_id,
                source_name=source_name,
                events_processed=existing_job.events_processed,
                events_failed=existing_job.events_failed,
                bytes_ingested=existing_job.bytes_ingested,
                is_duplicate_batch=True,
                message="Duplicate batch detected. Records from this identical payload were previously ingested.",
                rejected_summary=(
                    [RejectedRecordItem(**item) for item in existing_job.rejected_records]
                    if existing_job.rejected_records
                    else []
                ),
            )

        # 5. Resolve Log Source
        detected_source_type = (
            LogSourceType.APPLICATION_JSON if ext in (".json", ".jsonl") else LogSourceType.CUSTOM
        )
        log_source = self.get_or_create_default_source(source_id, detected_type=detected_source_type)

        # 6. Initialize Ingestion Job in RUNNING state
        job = IngestionJob(
            log_source_id=log_source.id,
            status=IngestionJobStatus.RUNNING,
            batch_identifier=batch_identifier,
            bytes_ingested=byte_length,
            events_processed=0,
            events_failed=0,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # 7. Select parser and parse content
        parser = self.select_parser(parser_type, content_str, field_mapping=field_mapping)
        parse_result = parser.parse_content(content_str)

        # Enforce maximum record count limit
        total_extracted = len(parse_result.valid_records) + len(parse_result.rejected_records)
        if total_extracted > settings.MAX_RECORDS_PER_IMPORT:
            job.status = IngestionJobStatus.FAILED
            job.error_message = f"Batch exceeds maximum record threshold of {settings.MAX_RECORDS_PER_IMPORT} records."
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=job.error_message,
            )

        # 8. Normalize records and collect validation rejections
        valid_schemas = []
        all_rejected: List[RejectedRecord] = list(parse_result.rejected_records)

        parser_name = (
            "auth" if isinstance(parser, AuthLogParser)
            else "firewall" if isinstance(parser, FirewallLogParser)
            else "generic"
        )

        for raw_rec in parse_result.valid_records:
            normalized_schema, rejection = self.normalizer.normalize(
                raw_rec,
                log_source_id=log_source.id,
                parser_type=parser_name,
            )
            if normalized_schema:
                valid_schemas.append(normalized_schema)
            elif rejection:
                all_rejected.append(rejection)

        # 9. Persist normalized events with duplicate hash prevention
        new_event_models = []
        duplicate_count = 0

        if valid_schemas:
            # Query existing event hashes to avoid duplicate collisions
            candidate_hashes = [s.event_hash for s in valid_schemas]
            existing_hashes = set(
                h[0]
                for h in self.db.query(NormalizedSecurityEvent.event_hash)
                .filter(NormalizedSecurityEvent.event_hash.in_(candidate_hashes))
                .all()
            )

            seen_in_batch = set()
            for schema in valid_schemas:
                if schema.event_hash in existing_hashes or schema.event_hash in seen_in_batch:
                    duplicate_count += 1
                    continue

                seen_in_batch.add(schema.event_hash)
                event_model = NormalizedSecurityEvent(
                    log_source_id=schema.log_source_id,
                    timestamp=schema.timestamp,
                    event_type=schema.event_type,
                    event_action=schema.event_action,
                    severity=schema.severity,
                    source_ip=schema.source_ip,
                    source_port=schema.source_port,
                    destination_ip=schema.destination_ip,
                    destination_port=schema.destination_port,
                    protocol=schema.protocol,
                    user_name=schema.user_name,
                    host_name=schema.host_name,
                    process_name=schema.process_name,
                    process_path=schema.process_path,
                    command_line=schema.command_line,
                    raw_payload=schema.raw_payload,
                    event_hash=schema.event_hash,
                    extra_fields=schema.extra_fields,
                )
                new_event_models.append(event_model)

            if new_event_models:
                self.db.add_all(new_event_models)

        # 10. Update Ingestion Job
        processed_count = len(new_event_models)
        failed_count = len(all_rejected)

        if failed_count == 0 and processed_count > 0:
            final_status = IngestionJobStatus.COMPLETED
        elif processed_count > 0 and failed_count > 0:
            final_status = IngestionJobStatus.PARTIALLY_FAILED
        elif processed_count == 0 and duplicate_count > 0 and failed_count == 0:
            final_status = IngestionJobStatus.COMPLETED
        else:
            final_status = IngestionJobStatus.FAILED

        rejected_dicts = [r.to_dict() for r in all_rejected]

        job.status = final_status
        job.events_processed = processed_count
        job.events_failed = failed_count
        job.rejected_records = rejected_dicts
        job.completed_at = datetime.now(timezone.utc)
        if failed_count > 0:
            job.error_message = f"{failed_count} malformed or invalid records rejected during validation."

        self.db.commit()
        self.db.refresh(job)

        msg_parts = [f"Imported {processed_count} new events successfully."]
        if duplicate_count > 0:
            msg_parts.append(f"{duplicate_count} duplicate events skipped.")
        if failed_count > 0:
            msg_parts.append(f"{failed_count} malformed records safely quarantined for analyst review.")

        return IngestionUploadResponse(
            job_id=job.id,
            status=job.status,
            source_id=log_source.id,
            source_name=log_source.name,
            events_processed=processed_count,
            events_failed=failed_count,
            bytes_ingested=byte_length,
            is_duplicate_batch=False,
            message=" ".join(msg_parts),
            rejected_summary=[RejectedRecordItem(**item) for item in rejected_dicts],
        )
