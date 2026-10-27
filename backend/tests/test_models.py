"""Unit tests validating database model constraints, relationships, and deduplication."""

import uuid
from datetime import datetime, timezone

import pytest
from app.models.alert import AlertStatus, SecurityAlert
from app.models.audit import AuditEvent
from app.models.event import EventSeverity, NormalizedSecurityEvent
from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    InvestigationNote,
    NoteType,
)
from app.models.log_source import (
    LogSource,
    LogSourceStatus,
    LogSourceType,
)
from app.models.rule import DetectionRule, RuleSeverity, RuleType
from app.models.user import User, UserRole, UserStatus
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_user_creation(db_session: Session):
    """Verifies user entity creation and defaults."""
    user = User(
        email="analyst@sentinel.sec",
        username="sec_analyst_1",
        hashed_password="argon2_hashed_placeholder",
        full_name="Alex Mercer",
        role=UserRole.ANALYST_TIER_1,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(User).filter_by(username="sec_analyst_1").first()
    assert retrieved is not None
    assert retrieved.email == "analyst@sentinel.sec"
    assert retrieved.role == UserRole.ANALYST_TIER_1
    assert retrieved.id is not None
    assert retrieved.created_at is not None


def test_duplicate_user_email_fails(db_session: Session):
    """Verifies unique email constraint on User model."""
    user1 = User(
        email="duplicate@sentinel.sec",
        username="user1",
        hashed_password="pw",
        full_name="User One",
    )
    user2 = User(
        email="duplicate@sentinel.sec",
        username="user2",
        hashed_password="pw",
        full_name="User Two",
    )
    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_event_deduplication_constraint(db_session: Session):
    """Verifies that duplicate event_hash triggers IntegrityError to prevent duplicate processing."""
    source = LogSource(
        name="Firewall-Edge-01",
        source_type=LogSourceType.SYSLOG,
        status=LogSourceStatus.ACTIVE,
    )
    db_session.add(source)
    db_session.commit()

    now = datetime.now(timezone.utc)
    event1 = NormalizedSecurityEvent(
        log_source_id=source.id,
        timestamp=now,
        event_type="network_flow",
        event_action="connection_denied",
        severity=EventSeverity.LOW,
        source_ip="192.168.1.50",
        destination_ip="10.0.0.1",
        raw_payload="Oct 27 12:00:00 fw BLOCK 192.168.1.50 -> 10.0.0.1",
        event_hash="hash_a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
    )
    db_session.add(event1)
    db_session.commit()

    # Attempting to insert identical event_hash must fail
    event2 = NormalizedSecurityEvent(
        log_source_id=source.id,
        timestamp=now,
        event_type="network_flow",
        event_action="connection_denied",
        severity=EventSeverity.LOW,
        source_ip="192.168.1.50",
        destination_ip="10.0.0.1",
        raw_payload="Oct 27 12:00:00 fw BLOCK 192.168.1.50 -> 10.0.0.1",
        event_hash="hash_a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
    )
    db_session.add(event2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_alert_and_incident_lifecycle(db_session: Session):
    """Verifies creation and relationship between rules, alerts, incidents, and notes."""
    analyst = User(
        email="lead@sentinel.sec",
        username="incident_commander",
        hashed_password="pw",
        full_name="Commander Shepard",
        role=UserRole.INCIDENT_RESPONDER,
    )
    db_session.add(analyst)
    db_session.commit()

    rule = DetectionRule(
        rule_code="RULE-AUTH-001",
        name="Multiple SSH Failed Logins",
        description="Detects > 5 failed SSH authentication attempts within 5 minutes.",
        severity=RuleSeverity.HIGH,
        rule_type=RuleType.THRESHOLD,
        rule_logic={"event_action": "login_failed", "threshold": 5, "window_seconds": 300},
        created_by_id=analyst.id,
    )
    db_session.add(rule)
    db_session.commit()

    incident = Incident(
        incident_number="INC-2026-0001",
        title="Brute Force Attack on Bastion Host",
        summary="Sustained SSH brute force observed from external IP targeting administrative accounts.",
        severity=IncidentSeverity.SEV_2_HIGH,
        status=IncidentStatus.OPEN,
        lead_analyst_id=analyst.id,
    )
    db_session.add(incident)
    db_session.commit()

    alert = SecurityAlert(
        rule_id=rule.id,
        title="SSH Brute Force Detected from 198.51.100.22",
        description="High volume of login failures against bastion.internal",
        severity=RuleSeverity.HIGH,
        status=AlertStatus.ESCALATED,
        deduplication_key=f"{rule.rule_code}:198.51.100.22:20261027",
        event_count=14,
        context_data={"attacker_ip": "198.51.100.22", "target_user": "root"},
        assigned_to_id=analyst.id,
        incident_id=incident.id,
    )
    db_session.add(alert)
    db_session.commit()

    note = InvestigationNote(
        incident_id=incident.id,
        author_id=analyst.id,
        note_type=NoteType.CONTAINMENT_ACTION,
        content="Applied perimeter firewall block rule for 198.51.100.22/32 at 20:45 UTC.",
    )
    db_session.add(note)
    db_session.commit()

    # Query incident and verify relationships
    saved_incident = db_session.query(Incident).filter_by(incident_number="INC-2026-0001").first()
    assert saved_incident is not None
    assert len(saved_incident.alerts) == 1
    assert saved_incident.alerts[0].title == alert.title
    assert len(saved_incident.notes) == 1
    assert saved_incident.notes[0].note_type == NoteType.CONTAINMENT_ACTION
    assert saved_incident.lead_analyst.username == "incident_commander"


def test_audit_event_logging(db_session: Session):
    """Verifies audit trail persistence for compliance tracking."""
    audit = AuditEvent(
        action="RULE_ACTIVATED",
        resource_type="detection_rule",
        resource_id=str(uuid.uuid4()),
        client_ip="10.10.10.5",
        user_agent="Sentinel-Console/1.0",
        details={"previous_state": "inactive", "new_state": "active"},
    )
    db_session.add(audit)
    db_session.commit()

    retrieved = db_session.query(AuditEvent).filter_by(action="RULE_ACTIVATED").first()
    assert retrieved is not None
    assert retrieved.client_ip == "10.10.10.5"
    assert retrieved.details["new_state"] == "active"
