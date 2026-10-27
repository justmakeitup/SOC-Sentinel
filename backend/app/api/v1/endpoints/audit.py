"""Audit trail endpoints for SOC compliance and administrative oversight."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models.audit import AuditEvent
from app.models.user import User, UserRole
from app.schemas.audit import AuditEventRead
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["Audit Log & Compliance"])


@router.get(
    "",
    response_model=PaginatedResponse[AuditEventRead],
    summary="List immutable audit trail events (Administrator and SOC Manager)",
)
def list_audit_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SOC_MANAGER])),
) -> PaginatedResponse[AuditEventRead]:
    """Retrieves chronological audit events for non-repudiation and forensic oversight."""
    query = db.query(AuditEvent)
    if action:
        query = query.filter(AuditEvent.action == action)
    if resource_type:
        query = query.filter(AuditEvent.resource_type == resource_type)

    total_count = query.count()
    events = (
        query.order_by(AuditEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return PaginatedResponse(
        items=[AuditEventRead.model_validate(e) for e in events],
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
