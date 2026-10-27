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
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    # Aliases for flexibility across subsystems
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_name: Optional[str] = None,
    actor_ip: Optional[str] = None,
) -> AuditEvent:
    """Appends an immutable audit entry into the regulatory ledger.

    Audit entries have no update or delete routes in ordinary application APIs.
    """
    resolved_resource_type = resource_type or entity_type or "system"
    resolved_resource_id = resource_id or entity_id
    resolved_client_ip = client_ip or actor_ip

    final_details = (details or {}).copy()
    if actor_name and "actor_name" not in final_details:
        final_details["actor_name"] = actor_name

    event = AuditEvent(
        actor_id=actor_id,
        action=action,
        resource_type=resolved_resource_type,
        resource_id=str(resolved_resource_id) if resolved_resource_id else None,
        client_ip=resolved_client_ip,
        user_agent=user_agent,
        details=final_details,
    )
    db.add(event)
    logger.info(
        "Audit [%s] target=%s:%s actor=%s",
        action,
        resolved_resource_type,
        resolved_resource_id,
        actor_id,
    )
    return event
