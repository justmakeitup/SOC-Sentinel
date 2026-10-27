"""Incident query endpoints for SOC case monitoring."""

from typing import Optional

from app.database import get_db
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.schemas.common import PaginatedResponse
from app.schemas.incident import IncidentRead
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/incidents", tags=["Incidents"])


class IncidentListItem(IncidentRead):
    lead_analyst_name: Optional[str] = None


@router.get(
    "",
    response_model=PaginatedResponse[IncidentListItem],
    status_code=status.HTTP_200_OK,
    summary="List active and closed incidents with status filters",
)
def list_incidents(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=50),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = Query(default=None),
) -> PaginatedResponse[IncidentListItem]:
    """Retrieves paginated incident case records."""
    query = db.query(Incident).options(
        joinedload(Incident.lead_analyst),
        joinedload(Incident.notes),
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

    total_count = query.with_entities(func.count(Incident.id)).scalar() or 0

    incidents = (
        query.order_by(Incident.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: list[IncidentListItem] = []
    for inc in incidents:
        analyst_name = inc.lead_analyst.full_name if inc.lead_analyst else "Unassigned"
        items.append(
            IncidentListItem(
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
                notes=[],
                lead_analyst_name=analyst_name,
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
