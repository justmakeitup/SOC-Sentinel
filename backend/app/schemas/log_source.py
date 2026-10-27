"""Pydantic validation schemas for log sources and ingestion tracking."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.log_source import IngestionJobStatus, LogSourceStatus, LogSourceType


class LogSourceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    source_type: LogSourceType
    description: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    retention_days: int = Field(default=90, ge=1, le=3650)
    config_metadata: Optional[dict] = None


class LogSourceCreate(LogSourceBase):
    pass


class LogSourceRead(LogSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: LogSourceStatus
    created_at: datetime
    updated_at: datetime


class IngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    log_source_id: UUID
    status: IngestionJobStatus
    batch_identifier: Optional[str] = None
    events_processed: int
    events_failed: int
    bytes_ingested: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
