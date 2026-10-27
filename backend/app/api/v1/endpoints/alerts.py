"""Security alerts query endpoints with filtering and pagination."""

from typing import Optional

from app.database import get_db
from app.models.alert import AlertStatus, SecurityAlert
from app.models.rule import DetectionRule, RuleSeverity
from app.schemas.alert import SecurityAlertRead
from app.schemas.common import PaginatedResponse
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/alerts", tags=["Security Alerts"])


class AlertListItem(SecurityAlertRead):
    rule_name: Optional[str] = None
    rule_code: Optional[str] = None
    source_ip: Optional[str] = None


@router.get(
    "",
    response_model=PaginatedResponse[AlertListItem],
    status_code=status.HTTP_200_OK,
    summary="List security alerts with search, severity, and status filters",
)
def list_alerts(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    severity: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None),
) -> PaginatedResponse[AlertListItem]:
    """Retrieves paginated alerts from the database.

    Returns empty list if no alerts match criteria.
    """
    query = db.query(SecurityAlert).options(joinedload(SecurityAlert.rule))

    if severity and severity.lower() != "all":
        try:
            sev_enum = RuleSeverity(severity.lower())
            query = query.filter(SecurityAlert.severity == sev_enum)
        except ValueError:
            pass

    if status_filter and status_filter.lower() != "all":
        try:
            st_enum = AlertStatus(status_filter.lower())
            query = query.filter(SecurityAlert.status == st_enum)
        except ValueError:
            pass

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.join(DetectionRule, SecurityAlert.rule_id == DetectionRule.id).filter(
            (SecurityAlert.title.ilike(term))
            | (DetectionRule.name.ilike(term))
            | (DetectionRule.rule_code.ilike(term))
            | (SecurityAlert.deduplication_key.ilike(term))
        )

    total_count = query.with_entities(func.count(SecurityAlert.id)).scalar() or 0

    alerts = (
        query.order_by(SecurityAlert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: list[AlertListItem] = []
    for a in alerts:
        src_ip = None
        if isinstance(a.context_data, dict):
            src_ip = (
                a.context_data.get("source_ip")
                or a.context_data.get("attacker_ip")
                or a.context_data.get("src_ip")
            )
        rule_name = a.rule.name if a.rule else "Unknown Rule"
        rule_code = a.rule.rule_code if a.rule else "N/A"

        item = AlertListItem(
            id=a.id,
            rule_id=a.rule_id,
            title=a.title,
            description=a.description,
            severity=a.severity,
            status=a.status,
            deduplication_key=a.deduplication_key,
            event_count=a.event_count,
            context_data=a.context_data or {},
            assigned_to_id=a.assigned_to_id,
            incident_id=a.incident_id,
            created_at=a.created_at,
            updated_at=a.updated_at,
            rule_name=rule_name,
            rule_code=rule_code,
            source_ip=src_ip or "—",
        )
        items.append(item)

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return PaginatedResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
