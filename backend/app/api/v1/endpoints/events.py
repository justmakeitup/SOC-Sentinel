"""Normalized security telemetry query endpoints with multi-attribute filtering."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.ingestion.schemas import NormalizedEventDetailResponse
from app.models.event import EventSeverity, NormalizedSecurityEvent
from app.schemas.common import PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/events", tags=["Security Events"])


@router.get(
    "",
    response_model=PaginatedResponse[NormalizedEventDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List normalized security events with date, type, severity, and IP filters",
)
def list_events(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source_id: Optional[UUID] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    source_ip: Optional[str] = Query(default=None),
    destination_ip: Optional[str] = Query(default=None),
    user_name: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
) -> PaginatedResponse[NormalizedEventDetailResponse]:
    """Retrieves paginated normalized security events."""
    query = db.query(NormalizedSecurityEvent).options(
        joinedload(NormalizedSecurityEvent.log_source)
    )

    if source_id:
        query = query.filter(NormalizedSecurityEvent.log_source_id == source_id)
    if event_type and event_type.lower() != "all":
        query = query.filter(NormalizedSecurityEvent.event_type.ilike(f"%{event_type}%"))
    if severity and severity.lower() != "all":
        try:
            sev_enum = EventSeverity(severity.lower())
            query = query.filter(NormalizedSecurityEvent.severity == sev_enum)
        except ValueError:
            pass
    if start_time:
        query = query.filter(NormalizedSecurityEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(NormalizedSecurityEvent.timestamp <= end_time)
    if source_ip:
        query = query.filter(NormalizedSecurityEvent.source_ip == source_ip)
    if destination_ip:
        query = query.filter(NormalizedSecurityEvent.destination_ip == destination_ip)
    if user_name:
        query = query.filter(NormalizedSecurityEvent.user_name.ilike(f"%{user_name}%"))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (NormalizedSecurityEvent.event_action.ilike(term))
            | (NormalizedSecurityEvent.user_name.ilike(term))
            | (NormalizedSecurityEvent.source_ip.ilike(term))
            | (NormalizedSecurityEvent.destination_ip.ilike(term))
            | (NormalizedSecurityEvent.host_name.ilike(term))
            | (NormalizedSecurityEvent.command_line.ilike(term))
        )

    total_count = query.with_entities(func.count(NormalizedSecurityEvent.id)).scalar() or 0

    events = (
        query.order_by(NormalizedSecurityEvent.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for ev in events:
        source_name = ev.log_source.name if ev.log_source else "Unknown"
        items.append(
            NormalizedEventDetailResponse(
                id=ev.id,
                log_source_id=ev.log_source_id,
                log_source_name=source_name,
                timestamp=ev.timestamp,
                ingested_at=ev.ingested_at,
                event_type=ev.event_type,
                event_action=ev.event_action,
                severity=ev.severity,
                source_ip=ev.source_ip,
                source_port=ev.source_port,
                destination_ip=ev.destination_ip,
                destination_port=ev.destination_port,
                protocol=ev.protocol,
                user_name=ev.user_name,
                host_name=ev.host_name,
                process_name=ev.process_name,
                process_path=ev.process_path,
                command_line=ev.command_line,
                raw_payload=ev.raw_payload,
                event_hash=ev.event_hash,
                extra_fields=ev.extra_fields,
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


@router.get(
    "/{event_id}",
    response_model=NormalizedEventDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch complete forensic details and raw payload for a normalized event",
)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
) -> NormalizedEventDetailResponse:
    """Retrieves full normalized event details."""
    ev = (
        db.query(NormalizedSecurityEvent)
        .options(joinedload(NormalizedSecurityEvent.log_source))
        .filter(NormalizedSecurityEvent.id == event_id)
        .first()
    )
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Normalized event '{event_id}' not found.",
        )

    source_name = ev.log_source.name if ev.log_source else "Unknown"
    return NormalizedEventDetailResponse(
        id=ev.id,
        log_source_id=ev.log_source_id,
        log_source_name=source_name,
        timestamp=ev.timestamp,
        ingested_at=ev.ingested_at,
        event_type=ev.event_type,
        event_action=ev.event_action,
        severity=ev.severity,
        source_ip=ev.source_ip,
        source_port=ev.source_port,
        destination_ip=ev.destination_ip,
        destination_port=ev.destination_port,
        protocol=ev.protocol,
        user_name=ev.user_name,
        host_name=ev.host_name,
        process_name=ev.process_name,
        process_path=ev.process_path,
        command_line=ev.command_line,
        raw_payload=ev.raw_payload,
        event_hash=ev.event_hash,
        extra_fields=ev.extra_fields,
    )
