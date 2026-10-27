"""Pydantic schemas for log ingestion and job tracking."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.event import EventSeverity
from app.models.log_source import IngestionJobStatus, LogSourceStatus, LogSourceType


class RejectedRecordItem(BaseModel):
    """Details of a malformed or invalid row rejected during ingestion."""
    line_number: int = Field(..., description="Line or record index within the imported file")
    reason: str = Field(..., description="Validation failure explanation")
    raw_snippet: Optional[str] = Field(default=None, description="Sanitized excerpt of rejected record")


class IngestionJobResponse(BaseModel):
    """Detailed summary of an ingestion job including rejection metrics."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    log_source_id: UUID
    status: IngestionJobStatus
    batch_identifier: Optional[str] = None
    events_processed: int
    events_failed: int
    bytes_ingested: int
    error_message: Optional[str] = None
    rejected_records: Optional[List[RejectedRecordItem]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class IngestionUploadResponse(BaseModel):
    """High-level outcome response returned immediately upon upload completion."""
    job_id: UUID
    status: IngestionJobStatus
    source_id: UUID
    source_name: str
    events_processed: int
    events_failed: int
    bytes_ingested: int
    is_duplicate_batch: bool = False
    message: str
    rejected_summary: Optional[List[RejectedRecordItem]] = None


class RawPayloadIngestRequest(BaseModel):
    """Direct JSON payload ingestion request."""
    source_id: Optional[UUID] = None
    source_name: Optional[str] = Field(default="Direct-API-Collector", max_length=100)
    parser_type: Optional[str] = Field(default="generic_json", description="auth | firewall | generic_json")
    records: List[Dict[str, Any]] = Field(..., min_length=1, description="List of raw event records")


class LogSourceResponse(BaseModel):
    """Log source details with total indexed events and job count."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: LogSourceType
    description: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    status: LogSourceStatus
    retention_days: int
    config_metadata: Optional[Dict[str, Any]] = None
    total_events: int = 0
    total_jobs: int = 0
    created_at: datetime
    updated_at: datetime


class LogSourceCreateRequest(BaseModel):
    """Schema for registering a new sensor collector or feed."""
    name: str = Field(..., min_length=2, max_length=100)
    source_type: LogSourceType
    description: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    retention_days: int = Field(default=90, ge=1, le=3650)
    config_metadata: Optional[Dict[str, Any]] = None


class NormalizedEventDetailResponse(BaseModel):
    """Comprehensive representation of a normalized security event."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    log_source_id: UUID
    log_source_name: Optional[str] = None
    timestamp: datetime
    ingested_at: datetime
    event_type: str
    event_action: str
    severity: EventSeverity
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    user_name: Optional[str] = None
    host_name: Optional[str] = None
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    command_line: Optional[str] = None
    raw_payload: str
    event_hash: str
    extra_fields: Optional[Dict[str, Any]] = None
