"""Log ingestion API endpoints for file uploads, direct streaming, and job inspection."""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingestion.schemas import (
    IngestionJobResponse,
    IngestionUploadResponse,
    RawPayloadIngestRequest,
    RejectedRecordItem,
)
from app.ingestion.service import IngestionService
from app.models.log_source import IngestionJob
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/ingestion", tags=["Log Ingestion"])


@router.post(
    "/upload",
    response_model=IngestionUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload security logs (CSV, JSON, NDJSON) for normalization and ingestion",
)
async def upload_log_file(
    file: UploadFile = File(...),
    source_id: Optional[UUID] = Form(default=None),
    parser_type: str = Form(default="auto", description="auto | auth | firewall | generic_json | csv"),
    field_mapping_json: Optional[str] = Form(default=None, description="Optional JSON string of column mappings"),
    db: Session = Depends(get_db),
) -> IngestionUploadResponse:
    """Imports, normalizes, validates, and persists telemetry logs.

    Rejects malformed records safely while capturing line-by-line failure reasons.
    """
    field_mapping = None
    if field_mapping_json:
        try:
            field_mapping = json.loads(field_mapping_json)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="field_mapping_json must be a valid JSON dictionary.",
            )

    content_bytes = await file.read()
    filename = file.filename or "uploaded_telemetry.log"

    service = IngestionService(db)
    return service.process_file_import(
        filename=filename,
        content_bytes=content_bytes,
        source_id=source_id,
        parser_type=parser_type,
        field_mapping=field_mapping,
    )


@router.post(
    "/raw",
    response_model=IngestionUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct JSON payload ingestion for streaming sensors",
)
def ingest_raw_records(
    payload: RawPayloadIngestRequest,
    db: Session = Depends(get_db),
) -> IngestionUploadResponse:
    """Ingests pre-structured JSON records directly from API forwards."""
    content_bytes = json.dumps(payload.records).encode("utf-8")
    service = IngestionService(db)
    return service.process_file_import(
        filename="direct_stream.json",
        content_bytes=content_bytes,
        source_id=payload.source_id,
        parser_type=payload.parser_type or "generic_json",
    )


@router.get(
    "/jobs",
    response_model=PaginatedResponse[IngestionJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List historical ingestion jobs with processing counts and health status",
)
def list_ingestion_jobs(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    source_id: Optional[UUID] = Query(default=None),
) -> PaginatedResponse[IngestionJobResponse]:
    """Retrieves paginated ingestion run records."""
    query = db.query(IngestionJob)
    if source_id:
        query = query.filter(IngestionJob.log_source_id == source_id)

    total_count = query.count()
    jobs = (
        query.order_by(IngestionJob.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for j in jobs:
        rejections = (
            [RejectedRecordItem(**r) for r in j.rejected_records]
            if j.rejected_records
            else []
        )
        items.append(
            IngestionJobResponse(
                id=j.id,
                log_source_id=j.log_source_id,
                status=j.status,
                batch_identifier=j.batch_identifier,
                events_processed=j.events_processed,
                events_failed=j.events_failed,
                bytes_ingested=j.bytes_ingested,
                error_message=j.error_message,
                rejected_records=rejections,
                started_at=j.started_at,
                completed_at=j.completed_at,
            )
        )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    return PaginatedResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect a specific ingestion job and its quarantined rejected records",
)
def get_ingestion_job(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> IngestionJobResponse:
    """Inspects detailed job outcome including malformed row error messages."""
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found.",
        )

    rejections = (
        [RejectedRecordItem(**r) for r in job.rejected_records]
        if job.rejected_records
        else []
    )
    return IngestionJobResponse(
        id=job.id,
        log_source_id=job.log_source_id,
        status=job.status,
        batch_identifier=job.batch_identifier,
        events_processed=job.events_processed,
        events_failed=job.events_failed,
        bytes_ingested=job.bytes_ingested,
        error_message=job.error_message,
        rejected_records=rejections,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
