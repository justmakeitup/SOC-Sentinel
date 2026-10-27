"""Pydantic validation schemas for security alerts."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertStatus
from app.models.rule import RuleSeverity


class SecurityAlertBase(BaseModel):
    rule_id: UUID
    title: str = Field(..., max_length=200)
    description: str
    severity: RuleSeverity
    status: AlertStatus = AlertStatus.NEW
    deduplication_key: str
    event_count: int = 1
    context_data: dict
    assigned_to_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None


class SecurityAlertRead(SecurityAlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
