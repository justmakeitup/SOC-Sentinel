"""Audit logging service for non-repudiation of SOC actions."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent

logger = logging.getLogger(__name__)


def record_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditEvent:
    """Appends an immutable audit entry into the regulatory ledger.

    Audit entries have no update or delete routes in ordinary application APIs.
    """
    event = AuditEvent(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        client_ip=client_ip,
        user_agent=user_agent,
        details=details or {},
    )
    db.add(event)
    logger.info("Audit [%s] target=%s:%s actor=%s", action, resource_type, resource_id, actor_id)
    return event
