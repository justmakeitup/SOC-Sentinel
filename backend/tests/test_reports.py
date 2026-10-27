"""Tests for Sentinel SOC reporting, analytics aggregations, MTTR metrics, and sanitized CSV exports."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.csv_exporter import sanitize_csv_cell
from app.models.alert import AlertStatus, SecurityAlert
from app.models.event import EventSeverity, NormalizedSecurityEvent
from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    InvestigationNote,
    NoteType,
)
from app.models.log_source import LogSource, LogSourceStatus, LogSourceType
from app.models.rule import DetectionRule, RuleSeverity, RuleType
from app.models.user import User, UserRole, UserStatus


@pytest.fixture
def reporting_source(db_session: Session) -> LogSource:
    source = LogSource(
        name="Corp-DC-Security",
        source_type=LogSourceType.WINDOWS_EVENT_LOG,
        status=LogSourceStatus.ACTIVE,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


@pytest.fixture
def reporting_rule(db_session: Session) -> DetectionRule:
    rule = DetectionRule(
        rule_code="SEC-TEST-001",
        name="Anomalous Domain Reconnaissance",
        description="Detects anomalous Active Directory LDAP enumeration",
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


# --------------------------------------------------------------------------
# 1. Formula Injection (CWE-1236) Neutralization Tests
# --------------------------------------------------------------------------

def test_csv_formula_injection_sanitization():
    """Cells beginning with formula operators (=, +, -, @, \\t, \\r) must be prefixed with apostrophe."""
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_csv_cell("+1+1") == "'+1+1"
    assert sanitize_csv_cell("-2+3+cmd|' /C calc'!A0") == "'-2+3+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    assert sanitize_csv_cell("\t=1+1") == "'\t=1+1"
    assert sanitize_csv_cell("\r=1+1") == "'\r=1+1"

    # Benign text should remain untouched
    assert sanitize_csv_cell("Authentication Failure: admin") == "Authentication Failure: admin"
    assert sanitize_csv_cell("192.168.1.100") == "192.168.1.100"
    assert sanitize_csv_cell(None) == ""
    assert sanitize_csv_cell(123) == "123"


# --------------------------------------------------------------------------
# 2. Empty Dataset Handling
# --------------------------------------------------------------------------

def test_operational_report_empty_database(client: TestClient):
    """An empty database returns zeroed operational counters and MTTR null metric."""
    resp = client.get("/api/v1/reports/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_events"] == 0
    assert data["total_alerts"] == 0
    assert data["total_incidents"] == 0
    assert data["event_volume_timeseries"] == []
    assert data["alerts_by_severity"]["critical"] == 0
    assert data["incidents_by_status"]["open"] == 0
    assert data["mttr_metrics"]["mean_time_to_resolve_minutes"] is None
    assert data["mttr_metrics"]["resolved_incidents_count"] == 0
    assert "Insufficient data" in data["mttr_metrics"]["sample_description"]
    assert "Mean Time to Resolution (MTTR)" in data["metric_definitions"]


# --------------------------------------------------------------------------
# 3. Invalid Date Range Handling
# --------------------------------------------------------------------------

def test_invalid_date_range_rejected(client: TestClient):
    """start_date > end_date returns HTTP 400 Bad Request."""
    resp = client.get(
        "/api/v1/reports/summary",
        params={
            "start_date": "2026-10-27T12:00:00Z",
            "end_date": "2026-10-20T12:00:00Z",
        },
    )
    assert resp.status_code == 400
    assert "cannot be after end_date" in resp.json()["detail"]


def test_malformed_date_format_rejected(client: TestClient):
    resp = client.get(
        "/api/v1/reports/summary",
        params={"start_date": "not-a-valid-date"},
    )
    assert resp.status_code == 400
    assert "Invalid start_date format" in resp.json()["detail"]


# --------------------------------------------------------------------------
# 4. Aggregations, Timeseries, & MTTR Calculation
# --------------------------------------------------------------------------

def test_operational_report_aggregations_and_mttr(
    client: TestClient,
    db_session: Session,
    reporting_source: LogSource,
    reporting_rule: DetectionRule,
):
    base_time = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Seed Normalized Events on 2 separate days
    events = [
        NormalizedSecurityEvent(
            log_source_id=reporting_source.id,
            timestamp=base_time,
            event_type="authentication",
            event_action="login_failed",
            severity=EventSeverity.HIGH,
            source_ip="192.168.1.15",
            raw_payload="{}",
            event_hash=uuid.uuid4().hex,
        ),
        NormalizedSecurityEvent(
            log_source_id=reporting_source.id,
            timestamp=base_time,
            event_type="authentication",
            event_action="login_failed",
            severity=EventSeverity.HIGH,
            source_ip="192.168.1.15",
            raw_payload="{}",
            event_hash=uuid.uuid4().hex,
        ),
        NormalizedSecurityEvent(
            log_source_id=reporting_source.id,
            timestamp=base_time + timedelta(days=1),
            event_type="network_flow",
            event_action="connection_denied",
            severity=EventSeverity.MEDIUM,
            source_ip="192.168.1.20",
            raw_payload="{}",
            event_hash=uuid.uuid4().hex,
        ),
    ]
    db_session.add_all(events)

    # 2. Seed Alerts
    alert = SecurityAlert(
        rule_id=reporting_rule.id,
        title="High Volume Recon",
        description="Suspicious queries detected",
        severity=RuleSeverity.HIGH,
        status=AlertStatus.NEW,
        deduplication_key=f"REP:{uuid.uuid4().hex[:8]}",
        event_count=2,
        context_data={"source_ip": "192.168.1.15"},
        created_at=base_time,
    )
    db_session.add(alert)

    # 3. Seed Incidents with known resolution times:
    # Case 1: Created at base_time, Resolved 60 minutes later (Duration: 60 mins)
    inc1 = Incident(
        incident_number="INC-2026-9001",
        title="Recon Incident Case",
        summary="Initial access probe",
        severity=IncidentSeverity.SEV_2_HIGH,
        status=IncidentStatus.RESOLVED,
        created_at=base_time,
        updated_at=base_time + timedelta(minutes=60),
    )
    # Case 2: Created at base_time, Closed 120 minutes later (Duration: 120 mins)
    inc2 = Incident(
        incident_number="INC-2026-9002",
        title="Contained Malicious Access",
        summary="User credentials revoked",
        severity=IncidentSeverity.SEV_3_MEDIUM,
        status=IncidentStatus.CLOSED,
        created_at=base_time,
        updated_at=base_time + timedelta(minutes=120),
    )
    # Case 3: Still open (Must NOT be counted in MTTR)
    inc3 = Incident(
        incident_number="INC-2026-9003",
        title="Ongoing Investigation",
        summary="Under review",
        severity=IncidentSeverity.SEV_1_CRITICAL,
        status=IncidentStatus.INVESTIGATING,
        created_at=base_time,
        updated_at=base_time,
    )
    db_session.add_all([inc1, inc2, inc3])
    db_session.commit()

    # Query Report
    resp = client.get(
        "/api/v1/reports/summary",
        params={
            "start_date": "2026-10-19T00:00:00Z",
            "end_date": "2026-10-25T00:00:00Z",
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_events"] == 3
    assert data["total_alerts"] == 1
    assert data["total_incidents"] == 3

    # Timeseries has 2 daily buckets
    assert len(data["event_volume_timeseries"]) == 2
    assert data["event_volume_timeseries"][0]["count"] == 2
    assert data["event_volume_timeseries"][1]["count"] == 1

    # Severity distribution
    assert data["alerts_by_severity"]["high"] == 1
    assert data["alerts_by_severity"]["critical"] == 0

    # Rule frequency
    assert len(data["alerts_by_rule"]) == 1
    assert data["alerts_by_rule"][0]["rule_code"] == "SEC-TEST-001"
    assert data["alerts_by_rule"][0]["count"] == 1

    # Incidents by status
    assert data["incidents_by_status"]["resolved"] == 1
    assert data["incidents_by_status"]["closed"] == 1
    assert data["incidents_by_status"]["investigating"] == 1

    # MTTR: Average of 60 mins and 120 mins = 90.0 mins (1.5 hours)
    mttr = data["mttr_metrics"]
    assert mttr["mean_time_to_resolve_minutes"] == 90.0
    assert mttr["mean_time_to_resolve_hours"] == 1.5
    assert mttr["resolved_incidents_count"] == 2
    assert "Calculated across 2 resolved/closed" in mttr["sample_description"]

    # Top IPs
    assert len(data["top_source_ips"]) > 0
    assert data["top_source_ips"][0]["ip"] == "192.168.1.15"
    assert data["top_source_ips"][0]["alert_count"] == 1


# --------------------------------------------------------------------------
# 5. Category & Source Filtering
# --------------------------------------------------------------------------

def test_operational_report_category_filtering(
    client: TestClient,
    db_session: Session,
    reporting_source: LogSource,
):
    now_utc = datetime.now(timezone.utc)
    ev1 = NormalizedSecurityEvent(
        log_source_id=reporting_source.id,
        timestamp=now_utc - timedelta(hours=2),
        event_type="authentication",
        event_action="login_success",
        severity=EventSeverity.INFORMATIONAL,
        raw_payload="{}",
        event_hash=uuid.uuid4().hex,
    )
    ev2 = NormalizedSecurityEvent(
        log_source_id=reporting_source.id,
        timestamp=now_utc - timedelta(hours=1),
        event_type="network_flow",
        event_action="flow_allow",
        severity=EventSeverity.INFORMATIONAL,
        raw_payload="{}",
        event_hash=uuid.uuid4().hex,
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    resp = client.get(
        "/api/v1/reports/summary",
        params={"event_category": "authentication"},
    )
    assert resp.status_code == 200
    assert resp.json()["total_events"] == 1


# --------------------------------------------------------------------------
# 6. CSV Export Endpoints & Formula Neutralization
# --------------------------------------------------------------------------

def test_csv_export_summary(client: TestClient):
    resp = client.get("/api/v1/reports/export?export_type=summary")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=sentinel_summary_report_" in resp.headers["content-disposition"]
    text = resp.text
    assert "Metric Category,Indicator Name,Calculated Value" in text
    assert "Total Security Events" in text
    assert "Mean Time to Resolution" in text


def test_csv_export_events_with_formula_injection_defense(
    client: TestClient,
    db_session: Session,
    reporting_source: LogSource,
):
    """Malicious formulas in fields must be neutralized with leading single quote."""
    now_utc = datetime.now(timezone.utc)
    malicious_event = NormalizedSecurityEvent(
        log_source_id=reporting_source.id,
        timestamp=now_utc,
        event_type="authentication",
        event_action="=cmd|' /C calc'!A0",  # Formula Injection Attempt
        user_name="+AdminDDEFormula",      # Formula Injection Attempt
        severity=EventSeverity.HIGH,
        raw_payload="{}",
        event_hash=uuid.uuid4().hex,
    )
    db_session.add(malicious_event)
    db_session.commit()

    resp = client.get("/api/v1/reports/export?export_type=events")
    assert resp.status_code == 200
    text = resp.text

    # Verify formula prefixes were neutralized
    assert "'=cmd|' /C calc'!A0" in text
    assert "'+AdminDDEFormula" in text


def test_csv_export_alerts_and_incidents(client: TestClient):
    resp_alerts = client.get("/api/v1/reports/export?export_type=alerts")
    assert resp_alerts.status_code == 200
    assert "Alert ID,Created At (UTC),Rule Code,Rule Name" in resp_alerts.text

    resp_inc = client.get("/api/v1/reports/export?export_type=incidents")
    assert resp_inc.status_code == 200
    assert "Incident Number,Created At (UTC),Updated At (UTC),Title" in resp_inc.text


# --------------------------------------------------------------------------
# 7. Incident Forensic Report Dossier Export
# --------------------------------------------------------------------------

def test_incident_dossier_markdown_export(
    client: TestClient,
    db_session: Session,
    reporting_rule: DetectionRule,
):
    """Generates complete forensic markdown dossier with metadata, alerts, and notes."""
    author = User(
        username="dossier_lead",
        email="dossier_lead@sentinel.org",
        full_name="Lead Analyst Dossier",
        hashed_password="mock_hashed_secret",
        role=UserRole.INCIDENT_RESPONDER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(author)
    db_session.commit()
    db_session.refresh(author)

    inc = Incident(
        incident_number="INC-2026-7788",
        title="APT Lateral Movement Containment",
        summary="Adversary compromised service account and probed SMB shares.",
        severity=IncidentSeverity.SEV_1_CRITICAL,
        status=IncidentStatus.CONTAINMENT,
        lead_analyst_id=author.id,
        containment_details="Port 445 blocked at border switch; service account token revoked.",
        lessons_learned="Implement LAPS across all server workloads.",
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)

    # Link an alert
    alt = SecurityAlert(
        rule_id=reporting_rule.id,
        title="Credential Spray Detected",
        description="Multiple logon failures",
        severity=RuleSeverity.CRITICAL,
        status=AlertStatus.ESCALATED,
        deduplication_key=f"SPRAY:{uuid.uuid4().hex[:8]}",
        event_count=10,
        context_data={},
        incident_id=inc.id,
    )
    # Link a note
    note = InvestigationNote(
        incident_id=inc.id,
        author_id=author.id,
        note_type=NoteType.CONTAINMENT_ACTION,
        content="Isolating host 10.0.1.20 from VLAN 5.",
    )
    db_session.add_all([alt, note])
    db_session.commit()

    resp = client.get(f"/api/v1/reports/incidents/{inc.id}/export")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "attachment; filename=incident_" in resp.headers["content-disposition"]

    md_text = resp.text
    assert "# Incident Investigation Dossier — INC-2026-7788" in md_text
    assert "APT Lateral Movement Containment" in md_text
    assert "Port 445 blocked at border switch" in md_text
    assert "Implement LAPS across all server workloads" in md_text
    assert "SEC-TEST-001" in md_text
    assert "Isolating host 10.0.1.20 from VLAN 5." in md_text
    assert "Chain of Custody & Non-Repudiation Verification" in md_text


def test_incident_dossier_not_found(client: TestClient):
    random_id = uuid.uuid4()
    resp = client.get(f"/api/v1/reports/incidents/{random_id}/export")
    assert resp.status_code == 404
    assert f"Incident with ID '{random_id}' not found" in resp.json()["detail"]


# --------------------------------------------------------------------------
# 8. Unauthenticated Access Rejection
# --------------------------------------------------------------------------

def test_unauthenticated_reports_denied(unauthenticated_client: TestClient):
    resp = unauthenticated_client.get("/api/v1/reports/summary")
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json()["detail"]

    export_resp = unauthenticated_client.get("/api/v1/reports/export")
    assert export_resp.status_code == 401
