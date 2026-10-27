"""Incident management service handling case workflows, state transitions, and audit trails."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.alert import AlertStatus, SecurityAlert
from app.models.audit import AuditEvent
from app.models.incident import Incident, IncidentSeverity, IncidentStatus, InvestigationNote
from app.models.user import User, UserRole
from app.schemas.alert import SecurityAlertRead
from app.schemas.incident import (
    IncidentCreate,
    IncidentDetailResponse,
    IncidentTimelineItem,
    IncidentUpdate,
    InvestigationNoteCreate,
    InvestigationNoteRead,
)
from app.services.audit_service import record_audit_event

logger = logging.getLogger(__name__)

ELEVATED_RESPONDER_ROLES = {
    UserRole.ANALYST_TIER_2,
    UserRole.INCIDENT_RESPONDER,
    UserRole.SOC_MANAGER,
    UserRole.ADMIN,
}


def generate_incident_number(db: Session) -> str:
    """Generates a sequential human-readable incident case code (e.g., 'INC-2026-0001')."""
    year = datetime.now(timezone.utc).year
    prefix = f"INC-{year}-"
    # Find existing incidents with this year prefix
    count = (
        db.query(func.count(Incident.id))
        .filter(Incident.incident_number.like(f"{prefix}%"))
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


def create_incident(
    db: Session,
    data: IncidentCreate,
    actor: User,
    client_ip: Optional[str] = None,
) -> Incident:
    """Creates a new incident case with transactional integrity and linked alerts."""
    # 1. Validate linked alerts if provided
    alerts_to_link: List[SecurityAlert] = []
    if data.alert_ids:
        alerts_to_link = (
            db.query(SecurityAlert)
            .filter(SecurityAlert.id.in_(data.alert_ids))
            .all()
        )
        if len(alerts_to_link) != len(data.alert_ids):
            found_ids = {a.id for a in alerts_to_link}
            missing = [str(aid) for aid in data.alert_ids if aid not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Security alert(s) not found: {', '.join(missing)}.",
            )

    # 2. Generate unique incident number if omitted
    incident_num = data.incident_number or generate_incident_number(db)

    # Check uniqueness
    existing = db.query(Incident).filter(Incident.incident_number == incident_num).first()
    if existing:
        incident_num = generate_incident_number(db)

    # 3. Create incident record
    incident = Incident(
        incident_number=incident_num,
        title=data.title,
        summary=data.summary,
        severity=data.severity or IncidentSeverity.SEV_3_MEDIUM,
        status=data.status or IncidentStatus.OPEN,
        lead_analyst_id=data.lead_analyst_id if data.lead_analyst_id else actor.id,
        containment_details=data.containment_details,
    )
    db.add(incident)
    db.flush()

    # 4. Link security alerts and escalate status
    for alert in alerts_to_link:
        alert.incident_id = incident.id
        alert.status = AlertStatus.ESCALATED

    # 5. Record immutable audit event
    record_audit_event(
        db=db,
        action="INCIDENT_CREATED",
        resource_type="incident",
        resource_id=str(incident.id),
        actor_id=actor.id,
        client_ip=client_ip,
        details={
            "incident_number": incident.incident_number,
            "title": incident.title,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "linked_alert_ids": [str(a.id) for a in alerts_to_link],
        },
    )

    db.commit()
    db.refresh(incident)
    logger.info("Created incident %s (ID: %s) by %s", incident.incident_number, incident.id, actor.username)
    return incident


def update_incident(
    db: Session,
    incident_id: UUID,
    data: IncidentUpdate,
    actor: User,
    client_ip: Optional[str] = None,
) -> Incident:
    """Updates incident status, severity, containment, or assignment with RBAC enforcement."""
    incident = (
        db.query(Incident)
        .options(joinedload(Incident.lead_analyst))
        .filter(Incident.id == incident_id)
        .first()
    )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )

    # RBAC Validation: Lifecycle transitions and severity modifications require elevated responder roles
    if data.status is not None or data.severity is not None or data.lead_analyst_id is not None:
        if actor.role not in ELEVATED_RESPONDER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions: Role '{actor.role.value}' cannot transition incident status or assign leads. "
                    "Requires Analyst Tier 2, Incident Responder, or SOC Manager."
                ),
            )

    audit_details: Dict[str, Any] = {}

    # Status transition
    if data.status is not None and data.status != incident.status:
        old_status = incident.status
        incident.status = data.status
        audit_details["status_transition"] = {
            "from": old_status.value,
            "to": data.status.value,
        }

        # Handle formal case closure
        if data.status == IncidentStatus.CLOSED:
            incident.closed_at = datetime.now(timezone.utc)
            record_audit_event(
                db=db,
                action="INCIDENT_CLOSED",
                resource_type="incident",
                resource_id=str(incident.id),
                actor_id=actor.id,
                client_ip=client_ip,
                details={"closed_at": incident.closed_at.isoformat()},
            )
        elif data.status == IncidentStatus.RESOLVED:
            record_audit_event(
                db=db,
                action="INCIDENT_RESOLVED",
                resource_type="incident",
                resource_id=str(incident.id),
                actor_id=actor.id,
                client_ip=client_ip,
                details={"containment_details": incident.containment_details},
            )
        else:
            incident.closed_at = None

        record_audit_event(
            db=db,
            action="INCIDENT_STATUS_CHANGED",
            resource_type="incident",
            resource_id=str(incident.id),
            actor_id=actor.id,
            client_ip=client_ip,
            details=audit_details["status_transition"],
        )

    # Severity modification
    if data.severity is not None and data.severity != incident.severity:
        old_sev = incident.severity
        incident.severity = data.severity
        audit_details["severity_change"] = {
            "from": old_sev.value,
            "to": data.severity.value,
        }
        record_audit_event(
            db=db,
            action="INCIDENT_SEVERITY_CHANGED",
            resource_type="incident",
            resource_id=str(incident.id),
            actor_id=actor.id,
            client_ip=client_ip,
            details=audit_details["severity_change"],
        )

    # Assignment change
    if data.lead_analyst_id is not None and data.lead_analyst_id != incident.lead_analyst_id:
        # Validate target user exists
        target_user = db.query(User).filter(User.id == data.lead_analyst_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{data.lead_analyst_id}' does not exist.",
            )
        old_analyst = incident.lead_analyst.full_name if incident.lead_analyst else "Unassigned"
        incident.lead_analyst_id = data.lead_analyst_id
        audit_details["assignment_change"] = {
            "from": old_analyst,
            "to": target_user.full_name,
            "lead_analyst_id": str(target_user.id),
        }
        record_audit_event(
            db=db,
            action="INCIDENT_ASSIGNED",
            resource_type="incident",
            resource_id=str(incident.id),
            actor_id=actor.id,
            client_ip=client_ip,
            details=audit_details["assignment_change"],
        )

    # Narrative content updates
    if data.title is not None:
        incident.title = data.title
    if data.summary is not None:
        incident.summary = data.summary
    if data.containment_details is not None:
        incident.containment_details = data.containment_details
        record_audit_event(
            db=db,
            action="INCIDENT_CONTAINMENT_UPDATED",
            resource_type="incident",
            resource_id=str(incident.id),
            actor_id=actor.id,
            client_ip=client_ip,
            details={"snippet": data.containment_details[:100]},
        )
    if data.lessons_learned is not None:
        incident.lessons_learned = data.lessons_learned
        record_audit_event(
            db=db,
            action="INCIDENT_LESSONS_LEARNED_UPDATED",
            resource_type="incident",
            resource_id=str(incident.id),
            actor_id=actor.id,
            client_ip=client_ip,
            details={"snippet": data.lessons_learned[:100]},
        )

    db.commit()
    db.refresh(incident)
    return incident


def add_investigation_note(
    db: Session,
    incident_id: UUID,
    note_data: InvestigationNoteCreate,
    actor: User,
    client_ip: Optional[str] = None,
) -> InvestigationNote:
    """Logs an immutable forensic journal entry on an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    note = InvestigationNote(
        incident_id=incident.id,
        author_id=actor.id,
        note_type=note_data.note_type,
        content=note_data.content,
    )
    db.add(note)
    db.flush()

    record_audit_event(
        db=db,
        action="INCIDENT_NOTE_ADDED",
        resource_type="incident",
        resource_id=str(incident.id),
        actor_id=actor.id,
        client_ip=client_ip,
        details={
            "note_id": str(note.id),
            "note_type": note.note_type.value,
            "snippet": note.content[:100],
        },
    )

    db.commit()
    db.refresh(note)
    return note


def link_alerts_to_incident(
    db: Session,
    incident_id: UUID,
    alert_ids: List[UUID],
    actor: User,
    client_ip: Optional[str] = None,
) -> Incident:
    """Associates one or more security alerts with an active incident case."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    alerts = db.query(SecurityAlert).filter(SecurityAlert.id.in_(alert_ids)).all()
    if len(alerts) != len(alert_ids):
        found = {a.id for a in alerts}
        missing = [str(aid) for aid in alert_ids if aid not in found]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert(s) not found: {', '.join(missing)}.",
        )

    for a in alerts:
        a.incident_id = incident.id
        a.status = AlertStatus.ESCALATED

    record_audit_event(
        db=db,
        action="INCIDENT_ALERTS_LINKED",
        resource_type="incident",
        resource_id=str(incident.id),
        actor_id=actor.id,
        client_ip=client_ip,
        details={"linked_alert_ids": [str(a.id) for a in alerts]},
    )

    db.commit()
    db.refresh(incident)
    return incident


def get_incident_detail(db: Session, incident_id: UUID) -> IncidentDetailResponse:
    """Builds a complete incident dossier including linked alerts, notes, and audit timeline."""
    incident = (
        db.query(Incident)
        .options(
            joinedload(Incident.lead_analyst),
            joinedload(Incident.notes).joinedload(InvestigationNote.author),
            joinedload(Incident.alerts).joinedload(SecurityAlert.rule),
        )
        .filter(Incident.id == incident_id)
        .first()
    )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )

    # 1. Notes serialized with author name
    serialized_notes: List[InvestigationNoteRead] = []
    for n in incident.notes:
        author_name = n.author.full_name if n.author else "SOC Analyst"
        serialized_notes.append(
            InvestigationNoteRead(
                id=n.id,
                incident_id=n.incident_id,
                author_id=n.author_id,
                author_name=author_name,
                note_type=n.note_type,
                content=n.content,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
        )

    # 2. Linked alerts
    serialized_alerts: List[SecurityAlertRead] = []
    distinct_event_ids = set()
    for a in incident.alerts:
        serialized_alerts.append(SecurityAlertRead.model_validate(a))
        if isinstance(a.context_data, dict):
            sids = a.context_data.get("supporting_event_ids", [])
            for sid in sids:
                distinct_event_ids.add(str(sid))

    # 3. Retrieve audit events for unified timeline
    audit_events = (
        db.query(AuditEvent)
        .options(joinedload(AuditEvent.actor))
        .filter(
            AuditEvent.resource_type == "incident",
            AuditEvent.resource_id == str(incident.id),
        )
        .order_by(AuditEvent.created_at.desc())
        .all()
    )

    timeline_items: List[IncidentTimelineItem] = []

    # Map audit events into timeline
    for aud in audit_events:
        actor_name = aud.actor.full_name if aud.actor else "System Automated"
        title = aud.action.replace("INCIDENT_", "").replace("_", " ").title()
        timeline_items.append(
            IncidentTimelineItem(
                id=str(aud.id),
                timestamp=aud.created_at,
                event_type="audit_event",
                title=f"Action: {title}",
                description=str(aud.details) if aud.details else None,
                actor_name=actor_name,
                metadata=aud.details or {},
            )
        )

    # Map investigation notes into timeline
    for note in incident.notes:
        author_name = note.author.full_name if note.author else "Analyst"
        timeline_items.append(
            IncidentTimelineItem(
                id=str(note.id),
                timestamp=note.created_at,
                event_type="investigation_note",
                title=f"Note: {note.note_type.value.replace('_', ' ').title()}",
                description=note.content,
                actor_name=author_name,
                metadata={"note_type": note.note_type.value},
            )
        )

    # Sort timeline chronologically descending (newest first)
    timeline_items.sort(key=lambda item: item.timestamp, reverse=True)

    lead_name = incident.lead_analyst.full_name if incident.lead_analyst else "Unassigned"

    return IncidentDetailResponse(
        id=incident.id,
        incident_number=incident.incident_number,
        title=incident.title,
        summary=incident.summary,
        severity=incident.severity,
        status=incident.status,
        lead_analyst_id=incident.lead_analyst_id,
        lead_analyst_name=lead_name,
        containment_details=incident.containment_details,
        lessons_learned=incident.lessons_learned,
        closed_at=incident.closed_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        notes=serialized_notes,
        alerts=serialized_alerts,
        timeline=timeline_items,
        linked_event_count=len(distinct_event_ids),
    )
