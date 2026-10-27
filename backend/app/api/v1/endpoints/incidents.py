"""Incident response case management endpoints following NIST SP 800-61 Rev 2."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.incident import (
    IncidentCreate,
    IncidentDetailResponse,
    IncidentLinkAlertsRequest,
    IncidentRead,
    IncidentTimelineItem,
    IncidentUpdate,
    InvestigationNoteCreate,
    InvestigationNoteRead,
)
from app.services import incident_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "",
    response_model=PaginatedResponse[IncidentRead],
    status_code=status.HTTP_200_OK,
    summary="List active and closed incidents with search, status, and severity filters",
)
def list_incidents(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="updated_at", pattern="^(created_at|updated_at|severity)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[IncidentRead]:
    """Retrieves paginated incident case records matching search query and filters."""
    query = db.query(Incident).options(
        joinedload(Incident.lead_analyst),
        joinedload(Incident.alerts),
    )

    if status_filter and status_filter.lower() != "all":
        try:
            st_enum = IncidentStatus(status_filter.lower())
            query = query.filter(Incident.status == st_enum)
        except ValueError:
            pass

    if severity and severity.lower() != "all":
        try:
            sev_enum = IncidentSeverity(severity.lower())
            query = query.filter(Incident.severity == sev_enum)
        except ValueError:
            pass

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Incident.title.ilike(term))
            | (Incident.incident_number.ilike(term))
            | (Incident.summary.ilike(term))
        )

    total_count = query.with_entities(func.count(Incident.id)).scalar() or 0

    order_col = getattr(Incident, sort_by)
    query = query.order_by(order_col.desc() if sort_dir == "desc" else order_col.asc())

    incidents = query.offset((page - 1) * page_size).limit(page_size).all()

    items: List[IncidentRead] = []
    for inc in incidents:
        analyst_name = inc.lead_analyst.full_name if inc.lead_analyst else "Unassigned"
        items.append(
            IncidentRead(
                id=inc.id,
                incident_number=inc.incident_number,
                title=inc.title,
                summary=inc.summary,
                severity=inc.severity,
                status=inc.status,
                lead_analyst_id=inc.lead_analyst_id,
                containment_details=inc.containment_details,
                lessons_learned=inc.lessons_learned,
                closed_at=inc.closed_at,
                created_at=inc.created_at,
                updated_at=inc.updated_at,
                lead_analyst_name=analyst_name,
                alerts_count=len(inc.alerts),
                notes=[],
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


@router.post(
    "",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident case, optionally linking initial security alerts",
)
def create_incident(
    data: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentDetailResponse:
    """Provisions a new incident response case and links specified alerts."""
    client_ip = request.client.host if request.client else None
    incident = incident_service.create_incident(
        db=db,
        data=data,
        actor=current_user,
        client_ip=client_ip,
    )
    return incident_service.get_incident_detail(db=db, incident_id=incident.id)


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
    summary="Get complete incident case dossier with timeline and linked telemetry",
)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> IncidentDetailResponse:
    """Retrieves full case details including timeline, linked alerts, and forensic notes."""
    return incident_service.get_incident_detail(db=db, incident_id=incident_id)


@router.patch(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
    summary="Update incident lifecycle status, containment, or assignment",
)
def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentDetailResponse:
    """Updates incident status or assignment with RBAC validation."""
    client_ip = request.client.host if request.client else None
    incident_service.update_incident(
        db=db,
        incident_id=incident_id,
        data=data,
        actor=current_user,
        client_ip=client_ip,
    )
    return incident_service.get_incident_detail(db=db, incident_id=incident_id)


@router.post(
    "/{incident_id}/notes",
    response_model=InvestigationNoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an immutable investigation note to the incident case file",
)
def add_note(
    incident_id: UUID,
    note_data: InvestigationNoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvestigationNoteRead:
    """Appends an analyst note to the case forensic journal."""
    client_ip = request.client.host if request.client else None
    note = incident_service.add_investigation_note(
        db=db,
        incident_id=incident_id,
        note_data=note_data,
        actor=current_user,
        client_ip=client_ip,
    )
    return InvestigationNoteRead(
        id=note.id,
        incident_id=note.incident_id,
        author_id=note.author_id,
        author_name=current_user.full_name,
        note_type=note.note_type,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.post(
    "/{incident_id}/alerts",
    response_model=IncidentDetailResponse,
    summary="Link additional security alerts to an active incident",
)
def link_alerts(
    incident_id: UUID,
    payload: IncidentLinkAlertsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentDetailResponse:
    """Associates security alerts with this incident and escalates their disposition."""
    client_ip = request.client.host if request.client else None
    incident_service.link_alerts_to_incident(
        db=db,
        incident_id=incident_id,
        alert_ids=payload.alert_ids,
        actor=current_user,
        client_ip=client_ip,
    )
    return incident_service.get_incident_detail(db=db, incident_id=incident_id)


@router.get(
    "/{incident_id}/timeline",
    response_model=List[IncidentTimelineItem],
    summary="Get unified investigation timeline combining notes and regulatory audit events",
)
def get_timeline(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> List[IncidentTimelineItem]:
    """Retrieves chronological audit and note events for this case file."""
    detail = incident_service.get_incident_detail(db=db, incident_id=incident_id)
    return detail.timeline
