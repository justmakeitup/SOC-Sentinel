"""API endpoints for SOC operational reporting, analytics aggregations, and sanitized exports."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.report import OperationalReportResponse
from app.services import report_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reporting & Analytics"])


@router.get(
    "/summary",
    response_model=OperationalReportResponse,
    summary="Compute operational security metrics and aggregations over a date range",
)
def get_operational_report(
    start_date: Optional[str] = Query(default=None, description="Start date in UTC (ISO 8601, e.g. 2026-10-01T00:00:00Z)"),
    end_date: Optional[str] = Query(default=None, description="End date in UTC (ISO 8601, e.g. 2026-10-27T23:59:59Z)"),
    event_category: Optional[str] = Query(default=None, description="Filter telemetry by category (e.g. authentication, network_flow)"),
    log_source_id: Optional[UUID] = Query(default=None, description="Filter telemetry by specific log source sensor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OperationalReportResponse:
    """Calculates operational security metrics from actual database telemetry records.

    Provides daily event volume timeseries, alert severity and rule distributions,
    incident lifecycle counts, and Mean Time to Resolution (MTTR).
    """
    return report_service.generate_operational_report(
        db=db,
        start_date=start_date,
        end_date=end_date,
        event_category=event_category,
        log_source_id=log_source_id,
    )


@router.get(
    "/export",
    summary="Export sanitized CSV report (summary, events, alerts, or incidents)",
)
def export_report_csv(
    export_type: str = Query(default="summary", pattern="^(summary|events|alerts|incidents)$"),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    event_category: Optional[str] = Query(default=None),
    log_source_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Exports filtered dataset as RFC 4180 CSV with formula injection protection (CWE-1236)."""
    now_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if export_type == "summary":
        report = report_service.generate_operational_report(
            db=db,
            start_date=start_date,
            end_date=end_date,
            event_category=event_category,
            log_source_id=log_source_id,
        )
        csv_content = report_service.export_summary_csv(report)
        filename = f"sentinel_summary_report_{now_stamp}.csv"

    elif export_type == "events":
        csv_content = report_service.export_events_csv(
            db=db,
            start_date=start_date,
            end_date=end_date,
            event_category=event_category,
            log_source_id=log_source_id,
        )
        filename = f"sentinel_events_export_{now_stamp}.csv"

    elif export_type == "alerts":
        csv_content = report_service.export_alerts_csv(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )
        filename = f"sentinel_alerts_export_{now_stamp}.csv"

    elif export_type == "incidents":
        csv_content = report_service.export_incidents_csv(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )
        filename = f"sentinel_incidents_export_{now_stamp}.csv"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export type '{export_type}'. Choose from: summary, events, alerts, incidents.",
        )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get(
    "/incidents/{incident_id}/export",
    summary="Download formal incident investigation report dossier in Markdown format",
)
def export_incident_report(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generates and downloads a complete incident response case file dossier.

    Contains case metadata, correlated alerts, raw telemetry evidence references,
    chronological investigation journal notes, containment details, and lessons learned.
    """
    markdown_dossier = report_service.export_incident_dossier_markdown(db, incident_id)
    filename = f"incident_{str(incident_id)[:8]}_investigation_dossier.md"

    return Response(
        content=markdown_dossier,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
