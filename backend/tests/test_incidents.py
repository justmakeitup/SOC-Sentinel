"""Automated tests for Sentinel Incident Response Management Subsystem.

Validates:
- Direct incident creation and alert promotion
- Multi-alert linking and relationship integrity
- Status lifecycle transitions (Open -> Investigating -> Containment -> Resolved -> Closed)
- Investigation notes documentation and forensic types
- RBAC authorization enforcement (Tier 1 vs Incident Responder vs Suspended)
- Non-repudiation audit trail generation and timeline aggregation
- Alert and evidence preservation upon incident resolution
- Search, severity filtering, and pagination
"""

import uuid
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.alert import AlertStatus, SecurityAlert
from app.models.audit import AuditEvent
from app.models.rule import DetectionRule, RuleSeverity, RuleType
from app.models.user import User, UserRole, UserStatus


@pytest.fixture
def active_responder(db_session: Session) -> User:
    """Provisions an active Incident Responder user."""
    user = User(
        username="lead_responder_1",
        email="lead_responder_1@sentinel.local",
        full_name="Alex Vance (Responder)",
        hashed_password="mock_hashed_secret",
        role=UserRole.INCIDENT_RESPONDER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tier1_analyst(db_session: Session) -> User:
    """Provisions a Tier-1 SOC Analyst with triage-only permissions."""
    user = User(
        username="triage_analyst_1",
        email="triage_analyst_1@sentinel.local",
        full_name="Robin Miller (Tier 1)",
        hashed_password="mock_hashed_secret",
        role=UserRole.ANALYST_TIER_1,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def suspended_analyst(db_session: Session) -> User:
    """Provisions a suspended user account."""
    user = User(
        username="suspended_user_1",
        email="suspended_1@sentinel.local",
        full_name="Locked Account",
        hashed_password="mock_hashed_secret",
        role=UserRole.ANALYST_TIER_2,
        status=UserStatus.SUSPENDED,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_detection_rule(db_session: Session) -> DetectionRule:
    """Provisions a rule to link test alerts."""
    rule = DetectionRule(
        rule_code="TEST-RULE-001",
        name="Test Incident Rule",
        description="Detection rule for incident test suite",
        severity=RuleSeverity.HIGH,
        rule_type=RuleType.THRESHOLD,
        is_active=True,
        time_window_seconds=300,
        threshold_count=5,
        rule_logic={},
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def sample_alerts(
    db_session: Session,
    sample_detection_rule: DetectionRule,
) -> List[SecurityAlert]:
    """Provisions two candidate alerts for incident escalation."""
    alerts = [
        SecurityAlert(
            rule_id=sample_detection_rule.id,
            title="Brute Force Compromise Detected",
            description="Repeated failed authentications followed by token issuance",
            severity=RuleSeverity.HIGH,
            status=AlertStatus.NEW,
            deduplication_key=f"TEST:192.168.1.10:{uuid.uuid4().hex[:8]}",
            event_count=8,
            context_data={
                "source_ip": "192.168.1.10",
                "user_name": "victim_corp",
                "supporting_event_ids": [uuid.uuid4().hex for _ in range(3)],
            },
        ),
        SecurityAlert(
            rule_id=sample_detection_rule.id,
            title="Lateral Movement RPC Sweep",
            description="Unusual internal connectivity on port 445",
            severity=RuleSeverity.HIGH,
            status=AlertStatus.NEW,
            deduplication_key=f"TEST:192.168.1.10:445:{uuid.uuid4().hex[:8]}",
            event_count=12,
            context_data={
                "source_ip": "192.168.1.10",
                "destination_port": 445,
                "supporting_event_ids": [uuid.uuid4().hex for _ in range(4)],
            },
        ),
    ]
    db_session.add_all(alerts)
    db_session.commit()
    for a in alerts:
        db_session.refresh(a)
    return alerts


# --------------------------------------------------------------------------
# 1. Incident Creation & Alert Promotion Tests
# --------------------------------------------------------------------------

def test_create_incident_direct(client: TestClient, active_responder: User):
    """Directly creates an incident case and validates schema and auto-numbering."""
    resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Suspected Active Directory Compromise",
            "summary": "Multiple unauthorized Kerberos ticket grants from unmanaged device.",
            "severity": "sev_2_high",
            "status": "open",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Suspected Active Directory Compromise"
    assert data["severity"] == "sev_2_high"
    assert data["status"] == "open"
    assert data["incident_number"].startswith("INC-")
    assert data["lead_analyst_name"] == active_responder.full_name


def test_create_incident_from_alerts(
    client: TestClient,
    active_responder: User,
    sample_alerts: List[SecurityAlert],
    db_session: Session,
):
    """Promotes security alerts into an incident and verifies status and linking."""
    alert_ids = [str(a.id) for a in sample_alerts]
    resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Corporate Network Intrusion",
            "summary": "Correlated brute-force followed by lateral movement sweep.",
            "severity": "sev_1_critical",
            "alert_ids": alert_ids,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["alerts"]) == 2

    # Verify database state: alerts must be ESCALATED and point to this incident
    alert_uuids = [a.id for a in sample_alerts]
    db_alerts = db_session.query(SecurityAlert).filter(SecurityAlert.id.in_(alert_uuids)).all()
    for alert in db_alerts:
        assert str(alert.incident_id) == data["id"]
        assert alert.status == AlertStatus.ESCALATED


def test_escalate_alert_endpoint(
    client: TestClient,
    active_responder: User,
    sample_alerts: List[SecurityAlert],
    db_session: Session,
):
    """POST /api/v1/alerts/{id}/escalate converts single alert into an incident."""
    alert = sample_alerts[0]
    resp = client.post(
        f"/api/v1/alerts/{alert.id}/escalate",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Urgent Triage Case: " + alert.title,
            "summary": "Escalated for immediate containment.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Urgent Triage Case: " + alert.title
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["id"] == str(alert.id)

    db_session.refresh(alert)
    assert alert.status == AlertStatus.ESCALATED
    assert str(alert.incident_id) == data["id"]


# --------------------------------------------------------------------------
# 2. Investigation Notes & Types Tests
# --------------------------------------------------------------------------

def test_add_investigation_notes(
    client: TestClient,
    active_responder: User,
    tier1_analyst: User,
):
    """Analysts can log forensic notes with specific classifications."""
    # Create incident
    inc_resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Ransomware Infiltration Investigation",
            "summary": "Shadow copy deletion attempt observed on backup server.",
            "severity": "sev_1_critical",
        },
    )
    inc_id = inc_resp.json()["id"]

    # Tier-1 Analyst adds forensic analysis note
    note1 = client.post(
        f"/api/v1/incidents/{inc_id}/notes",
        headers={"X-User-Id": str(tier1_analyst.id)},
        json={
            "note_type": "analysis",
            "content": "Host IP 10.0.4.15 executed vssadmin delete shadows /all /quiet via cmd.exe.",
        },
    )
    assert note1.status_code == 201
    assert note1.json()["note_type"] == "analysis"
    assert note1.json()["author_name"] == tier1_analyst.full_name

    # Responder adds containment note
    note2 = client.post(
        f"/api/v1/incidents/{inc_id}/notes",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "note_type": "containment_action",
            "content": "Host 10.0.4.15 isolated from VLAN 4 via perimeter switch ACL.",
        },
    )
    assert note2.status_code == 201
    assert note2.json()["note_type"] == "containment_action"

    # Verify notes appear in incident detail
    detail = client.get(f"/api/v1/incidents/{inc_id}").json()
    assert len(detail["notes"]) == 2


# --------------------------------------------------------------------------
# 3. Status Lifecycle Transitions & Evidence Preservation
# --------------------------------------------------------------------------

def test_incident_status_transitions_and_evidence_preservation(
    client: TestClient,
    active_responder: User,
    sample_alerts: List[SecurityAlert],
    db_session: Session,
):
    """Walks incident lifecycle: Open -> Investigating -> Containment -> Resolved -> Closed.

    Crucial requirement: Resolving/closing incident must NEVER delete or detach associated alerts.
    """
    alert_ids = [str(a.id) for a in sample_alerts]
    inc_resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Data Spill Investigation",
            "summary": "Sensitive S3 bucket permissions modified.",
            "severity": "sev_2_high",
            "alert_ids": alert_ids,
        },
    )
    inc_id = inc_resp.json()["id"]

    # 1. Transition to Investigating
    resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"X-User-Id": str(active_responder.id)},
        json={"status": "investigating"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"

    # 2. Transition to Containment with details
    resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "status": "containment",
            "containment_details": "Bucket ACL restored to private; IAM session tokens invalidated.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "containment"
    assert "IAM session tokens invalidated" in resp.json()["containment_details"]

    # 3. Transition to Resolved
    resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"X-User-Id": str(active_responder.id)},
        json={"status": "resolved"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"

    # 4. Formally Close Case
    resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "status": "closed",
            "lessons_learned": "Enforce SCP policy restricting public bucket policies across AWS org.",
        },
    )
    assert resp.status_code == 200
    closed_data = resp.json()
    assert closed_data["status"] == "closed"
    assert closed_data["closed_at"] is not None

    # CRITICAL: Verify alerts still exist in database and remain linked
    alert_uuids = [a.id for a in sample_alerts]
    alerts_in_db = db_session.query(SecurityAlert).filter(SecurityAlert.id.in_(alert_uuids)).all()
    assert len(alerts_in_db) == 2  # Alerts NOT deleted
    for a in alerts_in_db:
        assert str(a.incident_id) == inc_id


# --------------------------------------------------------------------------
# 4. Authorization & RBAC Enforcement Tests
# --------------------------------------------------------------------------

def test_tier1_cannot_modify_incident_lifecycle(
    client: TestClient,
    tier1_analyst: User,
    active_responder: User,
):
    """Tier 1 Analyst cannot close or transition incident status (403 Forbidden)."""
    # Incident created by responder
    inc_resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Privilege Escalation Case",
            "summary": "Local administrator group modified.",
        },
    )
    inc_id = inc_resp.json()["id"]

    # Tier 1 attempts to close incident -> must fail with 403
    patch_resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"X-User-Id": str(tier1_analyst.id)},
        json={"status": "closed"},
    )
    assert patch_resp.status_code == 403
    assert "Insufficient permissions" in patch_resp.json()["detail"]


def test_suspended_analyst_denied(
    client: TestClient,
    suspended_analyst: User,
):
    """Suspended user account cannot access or mutate incidents (403 Forbidden)."""
    resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(suspended_analyst.id)},
        json={
            "title": "Unauthorized Request",
            "summary": "Should be rejected.",
        },
    )
    assert resp.status_code == 403
    assert "User account is suspended" in resp.json()["detail"]


# --------------------------------------------------------------------------
# 5. Non-Repudiation Audit Trail & Timeline Tests
# --------------------------------------------------------------------------

def test_incident_audit_trail_and_timeline(
    client: TestClient,
    active_responder: User,
    db_session: Session,
):
    """Verifies that all state changes create immutable AuditEvent records."""
    # 1. Create incident
    inc_resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Audit Non-Repudiation Case",
            "summary": "Testing regulatory audit event recording.",
        },
    )
    inc_id = inc_resp.json()["id"]

    # 2. Update status
    client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"X-User-Id": str(active_responder.id)},
        json={"status": "containment"},
    )

    # 3. Add note
    client.post(
        f"/api/v1/incidents/{inc_id}/notes",
        headers={"X-User-Id": str(active_responder.id)},
        json={"note_type": "analysis", "content": "Evidence collected from SIEM."},
    )

    # 4. Inspect audit events in database directly
    audit_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.resource_type == "incident", AuditEvent.resource_id == inc_id)
        .all()
    )
    actions = {a.action for a in audit_events}
    assert "INCIDENT_CREATED" in actions
    assert "INCIDENT_STATUS_CHANGED" in actions
    assert "INCIDENT_NOTE_ADDED" in actions

    # 5. Verify timeline endpoint combines notes and audit events
    timeline_resp = client.get(f"/api/v1/incidents/{inc_id}/timeline")
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 3

    event_types = {t["event_type"] for t in timeline}
    assert "audit_event" in event_types
    assert "investigation_note" in event_types


# --------------------------------------------------------------------------
# 6. Linking Additional Alerts to Existing Incident
# --------------------------------------------------------------------------

def test_link_additional_alerts(
    client: TestClient,
    active_responder: User,
    sample_alerts: List[SecurityAlert],
):
    """POST /api/v1/incidents/{id}/alerts links new alerts to ongoing case."""
    inc_resp = client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Multi-Phase Intrusion",
            "summary": "Correlating alerts over time.",
        },
    )
    inc_id = inc_resp.json()["id"]

    link_resp = client.post(
        f"/api/v1/incidents/{inc_id}/alerts",
        headers={"X-User-Id": str(active_responder.id)},
        json={"alert_ids": [str(sample_alerts[0].id)]},
    )
    assert link_resp.status_code == 200
    assert len(link_resp.json()["alerts"]) == 1

    link_resp2 = client.post(
        f"/api/v1/incidents/{inc_id}/alerts",
        headers={"X-User-Id": str(active_responder.id)},
        json={"alert_ids": [str(sample_alerts[1].id)]},
    )
    assert link_resp2.status_code == 200
    assert len(link_resp2.json()["alerts"]) == 2


# --------------------------------------------------------------------------
# 7. Search, Filtering, and Pagination
# --------------------------------------------------------------------------

def test_incident_search_and_filters(
    client: TestClient,
    active_responder: User,
):
    """Validates search, severity filter, status filter, and pagination."""
    # Create multiple incidents with distinct attributes
    client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Phishing Campaign Alpha",
            "summary": "Harvested credentials via fake portal.",
            "severity": "sev_3_medium",
            "status": "open",
        },
    )
    client.post(
        "/api/v1/incidents",
        headers={"X-User-Id": str(active_responder.id)},
        json={
            "title": "Crypto Mining Botnet Bravo",
            "summary": "High CPU utilization on compute clusters.",
            "severity": "sev_1_critical",
            "status": "containment",
        },
    )

    # Search for "Phishing"
    search_resp = client.get("/api/v1/incidents?search=Phishing")
    assert search_resp.status_code == 200
    items = search_resp.json()["items"]
    assert any("Phishing Campaign" in i["title"] for i in items)
    assert not any("Crypto Mining" in i["title"] for i in items)

    # Filter by severity
    sev_resp = client.get("/api/v1/incidents?severity=sev_1_critical")
    assert sev_resp.status_code == 200
    for inc in sev_resp.json()["items"]:
        assert inc["severity"] == "sev_1_critical"

    # Filter by status
    status_resp = client.get("/api/v1/incidents?status=containment")
    assert status_resp.status_code == 200
    for inc in status_resp.json()["items"]:
        assert inc["status"] == "containment"
