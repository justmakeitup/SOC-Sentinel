"""Log sources management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.ingestion.schemas import LogSourceCreateRequest, LogSourceResponse
from app.models.event import NormalizedSecurityEvent
from app.models.log_source import IngestionJob, LogSource
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/sources", tags=["Log Sources"])


@router.get(
    "",
    response_model=PaginatedResponse[LogSourceResponse],
    status_code=status.HTTP_200_OK,
    summary="List registered log sources with indexed event volumes",
)
def list_sources(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> PaginatedResponse[LogSourceResponse]:
    """Retrieves paginated registered sensors and telemetry feeds."""
    total_count = db.query(LogSource).count()
    sources = (
        db.query(LogSource)
        .order_by(LogSource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for s in sources:
        event_count = (
            db.query(func.count(NormalizedSecurityEvent.id))
            .filter(NormalizedSecurityEvent.log_source_id == s.id)
            .scalar()
            or 0
        )
        job_count = (
            db.query(func.count(IngestionJob.id))
            .filter(IngestionJob.log_source_id == s.id)
            .scalar()
            or 0
        )
        items.append(
            LogSourceResponse(
                id=s.id,
                name=s.name,
                source_type=s.source_type,
                description=s.description,
                ip_address=s.ip_address,
                hostname=s.hostname,
                status=s.status,
                retention_days=s.retention_days,
                config_metadata=s.config_metadata,
                total_events=event_count,
                total_jobs=job_count,
                created_at=s.created_at,
                updated_at=s.updated_at,
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
    response_model=LogSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new telemetry log source or sensor",
)
def create_source(
    payload: LogSourceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.DETECTION_ENGINEER, UserRole.ADMIN])
    ),
) -> LogSourceResponse:
    """Registers a new sensor forwarder."""
    existing = db.query(LogSource).filter(LogSource.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A log source with name '{payload.name}' already exists.",
        )

    source = LogSource(
        name=payload.name,
        source_type=payload.source_type,
        description=payload.description,
        ip_address=payload.ip_address,
        hostname=payload.hostname,
        retention_days=payload.retention_days,
        config_metadata=payload.config_metadata,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    return LogSourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        description=source.description,
        ip_address=source.ip_address,
        hostname=source.hostname,
        status=source.status,
        retention_days=source.retention_days,
        config_metadata=source.config_metadata,
        total_events=0,
        total_jobs=0,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.get(
    "/{source_id}",
    response_model=LogSourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch log source details and sensor configuration",
)
def get_source(
    source_id: UUID,
    db: Session = Depends(get_db),
) -> LogSourceResponse:
    """Inspects a specific log source."""
    source = db.query(LogSource).filter(LogSource.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LogSource '{source_id}' not found.",
        )

    event_count = (
        db.query(func.count(NormalizedSecurityEvent.id))
        .filter(NormalizedSecurityEvent.log_source_id == source.id)
        .scalar()
        or 0
    )
    job_count = (
        db.query(func.count(IngestionJob.id))
        .filter(IngestionJob.log_source_id == source.id)
        .scalar()
        or 0
    )

    return LogSourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        description=source.description,
        ip_address=source.ip_address,
        hostname=source.hostname,
        status=source.status,
        retention_days=source.retention_days,
        config_metadata=source.config_metadata,
        total_events=event_count,
        total_jobs=job_count,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )
