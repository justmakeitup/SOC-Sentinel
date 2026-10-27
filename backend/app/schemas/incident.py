"""Pydantic validation schemas for incident case files and investigation notes."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.incident import IncidentSeverity, IncidentStatus, NoteType


class InvestigationNoteBase(BaseModel):
    note_type: NoteType = NoteType.GENERAL
    content: str = Field(..., min_length=1)


class InvestigationNoteCreate(InvestigationNoteBase):
    pass


class InvestigationNoteRead(InvestigationNoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime


class IncidentBase(BaseModel):
    incident_number: str = Field(..., max_length=32)
    title: str = Field(..., max_length=200)
    summary: str
    severity: IncidentSeverity = IncidentSeverity.SEV_3_MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    lead_analyst_id: Optional[UUID] = None
    containment_details: Optional[str] = None
    lessons_learned: Optional[str] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentRead(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    notes: List[InvestigationNoteRead] = []
