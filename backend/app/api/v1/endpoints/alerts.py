"""Security alerts query endpoints with filtering, triage updates, and evidence inspection."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.engine.schemas import AlertDetailResponse, AlertStatusUpdateRequest
from app.models.alert import AlertStatus, SecurityAlert
from app.models.event import NormalizedSecurityEvent
from app.models.rule import DetectionRule, RuleSeverity
from app.schemas.alert import SecurityAlertRead
from app.schemas.common import PaginatedResponse

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
            # Check affected entities
            aff = a.context_data.get("affected_entities")
            if not src_ip and isinstance(aff, dict):
                src_ip = aff.get("source_ip")

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


@router.get(
    "/{alert_id}",
    response_model=AlertDetailResponse,
    summary="Get alert detail with evidence and supporting event records",
)
def get_alert_detail(
    alert_id: UUID,
    db: Session = Depends(get_db),
) -> AlertDetailResponse:
    """Retrieves full alert context including supporting event records for verification."""
    alert = (
        db.query(SecurityAlert)
        .options(joinedload(SecurityAlert.rule))
        .filter(SecurityAlert.id == alert_id)
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security alert '{alert_id}' not found.",
        )

    # Resolve supporting events
    ctx = alert.context_data or {}
    supporting_raw_ids = ctx.get("supporting_event_ids", [])
    supporting_events_data: List[Dict[str, Any]] = []

    valid_uuids: List[UUID] = []
    for sid in supporting_raw_ids:
        try:
            valid_uuids.append(UUID(str(sid)))
        except (ValueError, TypeError):
            continue

    if valid_uuids:
        events = (
            db.query(NormalizedSecurityEvent)
            .filter(NormalizedSecurityEvent.id.in_(valid_uuids))
            .order_by(NormalizedSecurityEvent.timestamp.asc())
            .all()
        )
        for ev in events:
            supporting_events_data.append({
                "id": str(ev.id),
                "timestamp": ev.timestamp.isoformat(),
                "event_type": ev.event_type,
                "event_action": ev.event_action,
                "severity": ev.severity.value if hasattr(ev.severity, "value") else str(ev.severity),
                "source_ip": ev.source_ip,
                "destination_ip": ev.destination_ip,
                "destination_port": ev.destination_port,
                "user_name": ev.user_name,
            })

    rule_code = alert.rule.rule_code if alert.rule else ctx.get("rule_code")
    rule_name = alert.rule.name if alert.rule else ctx.get("rule_name")

    return AlertDetailResponse(
        id=alert.id,
        rule_id=alert.rule_id,
        rule_code=rule_code,
        rule_name=rule_name,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        deduplication_key=alert.deduplication_key,
        event_count=alert.event_count,
        context_data=ctx,
        assigned_to_id=alert.assigned_to_id,
        incident_id=alert.incident_id,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        supporting_events=supporting_events_data,
    )


@router.patch(
    "/{alert_id}/status",
    response_model=AlertDetailResponse,
    summary="Update alert triage disposition status",
)
def update_alert_status(
    alert_id: UUID,
    status_update: AlertStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> AlertDetailResponse:
    """Updates the lifecycle status of an alert (e.g. triaged, investigating, closed)."""
    alert = (
        db.query(SecurityAlert)
        .options(joinedload(SecurityAlert.rule))
        .filter(SecurityAlert.id == alert_id)
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security alert '{alert_id}' not found.",
        )

    alert.status = status_update.status
    db.commit()
    db.refresh(alert)

    return get_alert_detail(alert_id=alert_id, db=db)
