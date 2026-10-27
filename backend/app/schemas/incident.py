"""Pydantic validation schemas for incident case files, investigation notes, and timelines."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.incident import IncidentSeverity, IncidentStatus, NoteType
from app.schemas.alert import SecurityAlertRead


class InvestigationNoteBase(BaseModel):
    """Core attributes of an analyst forensic note."""

    note_type: NoteType = NoteType.GENERAL
    content: str = Field(..., min_length=1)


class InvestigationNoteCreate(InvestigationNoteBase):
    """Payload for submitting a new investigation note."""

    pass


class InvestigationNoteRead(InvestigationNoteBase):
    """Serialized forensic note with author attribution."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    author_id: UUID
    author_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncidentBase(BaseModel):
    """Common incident attributes."""

    title: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=3)
    severity: IncidentSeverity = IncidentSeverity.SEV_3_MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    lead_analyst_id: Optional[UUID] = None
    containment_details: Optional[str] = None
    lessons_learned: Optional[str] = None


class IncidentCreate(BaseModel):
    """Payload for creating a new incident case, optionally linking initial security alerts."""

    title: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=3)
    severity: Optional[IncidentSeverity] = IncidentSeverity.SEV_3_MEDIUM
    status: Optional[IncidentStatus] = IncidentStatus.OPEN
    lead_analyst_id: Optional[UUID] = None
    incident_number: Optional[str] = Field(default=None, max_length=32)
    alert_ids: Optional[List[UUID]] = Field(default_factory=list)
    containment_details: Optional[str] = None


class IncidentUpdate(BaseModel):
    """Tunable parameters for updating incident lifecycle status, containment, or assignment."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    summary: Optional[str] = Field(default=None, min_length=3)
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    lead_analyst_id: Optional[UUID] = None
    containment_details: Optional[str] = None
    lessons_learned: Optional[str] = None


class IncidentLinkAlertsRequest(BaseModel):
    """Payload for associating one or more security alerts with an active incident."""

    alert_ids: List[UUID] = Field(..., min_length=1)


class IncidentTimelineItem(BaseModel):
    """Unified chronological record representing an investigation note, status change, or linked alert."""

    id: str
    timestamp: datetime
    event_type: str  # 'investigation_note', 'status_change', 'alert_linked', 'containment', 'assignment'
    title: str
    description: Optional[str] = None
    actor_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentRead(IncidentBase):
    """Standard representation of an incident case in list queries."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_number: str
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lead_analyst_name: Optional[str] = None
    alerts_count: int = 0
    notes: List[InvestigationNoteRead] = []


class IncidentDetailResponse(IncidentBase):
    """Comprehensive case file including linked alerts, chronological notes, and audit timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_number: str
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lead_analyst_name: Optional[str] = None
    notes: List[InvestigationNoteRead] = []
    alerts: List[SecurityAlertRead] = []
    timeline: List[IncidentTimelineItem] = []
    linked_event_count: int = 0
