"""Dashboard metrics and aggregated telemetry overview endpoints."""

from datetime import datetime, timezone

from app.database import get_db
from app.models.alert import AlertStatus, SecurityAlert
from app.models.event import NormalizedSecurityEvent
from app.models.incident import Incident, IncidentStatus
from app.models.rule import RuleSeverity
from app.schemas.dashboard import DashboardSummaryResponse, TimeSeriesPoint
from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dashboard", tags=["SOC Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch live SOC operational metrics and aggregate counts",
)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    """Calculates operational counters from normalized events, alerts, and incidents.

    Returns zeroed metrics if the database has not yet received telemetry.
    """
    # 1. Total events processed
    events_count = db.query(func.count(NormalizedSecurityEvent.id)).scalar() or 0

    # 2. Active alerts (new, triaged, investigating)
    active_statuses = [
        AlertStatus.NEW,
        AlertStatus.TRIAGED,
        AlertStatus.INVESTIGATING,
    ]
    active_alerts_count = (
        db.query(func.count(SecurityAlert.id))
        .filter(SecurityAlert.status.in_(active_statuses))
        .scalar()
        or 0
    )

    # 3. Open incidents (non-closed)
    open_incidents_count = (
        db.query(func.count(Incident.id))
        .filter(Incident.status != IncidentStatus.CLOSED)
        .scalar()
        or 0
    )

    # 4. Critical alerts
    critical_alerts_count = (
        db.query(func.count(SecurityAlert.id))
        .filter(
            SecurityAlert.severity == RuleSeverity.CRITICAL,
            SecurityAlert.status.in_(active_statuses),
        )
        .scalar()
        or 0
    )

    # 5. Severity distribution across active alerts
    sev_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "informational": 0,
    }
    sev_rows = (
        db.query(SecurityAlert.severity, func.count(SecurityAlert.id))
        .group_by(SecurityAlert.severity)
        .all()
    )
    for sev_enum, count in sev_rows:
        sev_name = sev_enum.value.lower() if hasattr(sev_enum, "value") else str(sev_enum).lower()
        if sev_name in sev_counts:
            sev_counts[sev_name] = count

    # 6. Event timeseries - fetch recent aggregated event volume if records exist
    timeseries_points: list[TimeSeriesPoint] = []
    # If no events exist, return empty list (UI shows clean empty state)
    if events_count > 0:
        recent_events = (
            db.query(
                func.strftime("%Y-%m-%d %H:00", NormalizedSecurityEvent.timestamp).label("hour"),
                func.count(NormalizedSecurityEvent.id),
            )
            .group_by("hour")
            .order_by("hour")
            .limit(24)
            .all()
        )
        for hour_str, count in recent_events:
            timeseries_points.append(
                TimeSeriesPoint(timestamp=str(hour_str), count=count)
            )

    return DashboardSummaryResponse(
        events_processed=events_count,
        active_alerts=active_alerts_count,
        open_incidents=open_incidents_count,
        critical_alerts=critical_alerts_count,
        event_volume_timeseries=timeseries_points,
        severity_distribution=sev_counts,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )
