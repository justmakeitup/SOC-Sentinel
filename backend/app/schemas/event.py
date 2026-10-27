"""Pydantic validation schemas for normalized security telemetry."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.event import EventSeverity


class NormalizedSecurityEventBase(BaseModel):
    log_source_id: UUID
    timestamp: datetime
    event_type: str = Field(..., max_length=64)
    event_action: str = Field(..., max_length=64)
    severity: EventSeverity = EventSeverity.INFORMATIONAL
    source_ip: Optional[str] = None
    source_port: Optional[int] = Field(default=None, ge=1, le=65535)
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = Field(default=None, ge=1, le=65535)
    protocol: Optional[str] = None
    user_name: Optional[str] = None
    host_name: Optional[str] = None
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    command_line: Optional[str] = None
    raw_payload: str
    extra_fields: Optional[dict] = None


class NormalizedSecurityEventCreate(NormalizedSecurityEventBase):
    pass


class NormalizedSecurityEventRead(NormalizedSecurityEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingested_at: datetime
    event_hash: str
