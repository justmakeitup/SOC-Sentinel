"""Comprehensive unit tests for the Sentinel Detection Engine and rules.

Validates:
- Rule 1 (Repeated Failed Logins): True positive, true negative, sliding window boundary.
- Rule 2 (Login After Failures): Correlation, chronological ordering, true negative.
- Rule 3 (Port Scan): Multi-port threshold, single-port non-detection, time window.
- Rule 4 (Unusual Auth): Multi-IP velocity, off-hours privileged access.
- Alert Deduplication & Cooldown: Suppression window, event_count increment, no alert storms.
- Robustness: Missing fields, null values, execution error isolation.
- Engine Replay and API endpoints.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.engine.base import BaseDetectionRule, RuleContext
from app.engine.correlator import DetectionEngine
from app.engine.registry import RuleRegistry
from app.engine.rules import (
    LoginAfterFailuresRule,
    PortScanRule,
    RepeatedFailedLoginsRule,
    UnusualAuthRule,
)
from app.models.alert import SecurityAlert
from app.models.event import EventSeverity, NormalizedSecurityEvent
from app.models.log_source import LogSource, LogSourceStatus, LogSourceType
from app.models.rule import RuleSeverity, RuleType


@pytest.fixture
def test_log_source(db_session: Session) -> LogSource:
    """Provisions a dummy log source for test event foreign key linkage."""
    source = LogSource(
        name="Test-Telemetry-Feed",
        source_type=LogSourceType.APPLICATION_JSON,
        description="Synthetic telemetry for detection engine unit tests",
        status=LogSourceStatus.ACTIVE,
        retention_days=30,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


def make_event(
    log_source_id: uuid.UUID,
    timestamp: datetime,
    event_type: str = "authentication",
    event_action: str = "login_failed",
    source_ip: str = "192.168.1.100",
    destination_ip: str = "10.0.0.5",
    destination_port: int = None,
    user_name: str = "alice",
    severity: EventSeverity = EventSeverity.LOW,
) -> NormalizedSecurityEvent:
    """Factory helper creating ephemeral NormalizedSecurityEvent instances."""
    return NormalizedSecurityEvent(
        id=uuid.uuid4(),
        log_source_id=log_source_id,
        timestamp=timestamp,
        event_type=event_type,
        event_action=event_action,
        severity=severity,
        source_ip=source_ip,
        destination_ip=destination_ip,
        destination_port=destination_port,
        user_name=user_name,
        event_hash=uuid.uuid4().hex,
        raw_payload='{"mock": true}',
    )


# --------------------------------------------------------------------------
# Rule 1: Repeated Failed Logins Unit Tests
# --------------------------------------------------------------------------

def test_rule1_repeated_failed_logins_true_positive(test_log_source: LogSource):
    """5 failed logins within 300 seconds triggers Rule 1."""
    rule = RepeatedFailedLoginsRule(threshold_count=5, time_window_seconds=300)
    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 20),
            event_type="authentication",
            event_action="login_failed",
            source_ip="203.0.113.15",
            user_name="victim_user",
        )
        for i in range(5)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_code == "SEC-AUTH-001"
    assert f.severity == RuleSeverity.HIGH
    assert f.affected_entities["user_name"] == "victim_user"
    assert f.affected_entities["source_ip"] == "203.0.113.15"
    assert len(f.supporting_event_ids) == 5
    assert f.evidence["failed_attempts"] == 5


def test_rule1_repeated_failed_logins_true_negative_below_threshold(test_log_source: LogSource):
    """4 failed logins (below threshold of 5) does NOT trigger Rule 1."""
    rule = RepeatedFailedLoginsRule(threshold_count=5, time_window_seconds=300)
    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 30),
            event_type="authentication",
            event_action="login_failed",
            source_ip="203.0.113.15",
            user_name="victim_user",
        )
        for i in range(4)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


def test_rule1_time_window_boundary(test_log_source: LogSource):
    """5 failed logins spread across 15 minutes (outside 300s window) does NOT trigger Rule 1."""
    rule = RepeatedFailedLoginsRule(threshold_count=5, time_window_seconds=300)
    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    # 1 attempt every 3 minutes (180s) -> total spread 720s
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 180),
            event_type="authentication",
            event_action="login_failed",
            source_ip="203.0.113.15",
            user_name="victim_user",
        )
        for i in range(5)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


# --------------------------------------------------------------------------
# Rule 2: Login After Failures Unit Tests
# --------------------------------------------------------------------------

def test_rule2_login_after_failures_true_positive(test_log_source: LogSource):
    """3 failed logins followed chronologically by 1 success triggers Rule 2."""
    rule = LoginAfterFailuresRule(threshold_count=3, time_window_seconds=600)
    base_time = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=0),
            event_type="authentication",
            event_action="login_failed",
            user_name="finance_user",
            source_ip="198.51.100.5",
        ),
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=30),
            event_type="authentication",
            event_action="login_failed",
            user_name="finance_user",
            source_ip="198.51.100.5",
        ),
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=60),
            event_type="authentication",
            event_action="login_failed",
            user_name="finance_user",
            source_ip="198.51.100.5",
        ),
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=90),
            event_type="authentication",
            event_action="login_success",
            user_name="finance_user",
            source_ip="198.51.100.5",
        ),
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_code == "SEC-AUTH-002"
    assert f.severity == RuleSeverity.MEDIUM
    assert f.evidence["preceding_failed_count"] == 3
    assert len(f.supporting_event_ids) == 4  # 3 fails + 1 success


def test_rule2_login_after_failures_true_negative_no_success(test_log_source: LogSource):
    """3 failed logins with NO subsequent success does NOT trigger Rule 2."""
    rule = LoginAfterFailuresRule(threshold_count=3, time_window_seconds=600)
    base_time = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 30),
            event_type="authentication",
            event_action="login_failed",
            user_name="finance_user",
        )
        for i in range(3)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


def test_rule2_success_before_failures_no_trigger(test_log_source: LogSource):
    """Success occurring BEFORE failures does NOT trigger Rule 2."""
    rule = LoginAfterFailuresRule(threshold_count=3, time_window_seconds=600)
    base_time = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            base_time,
            event_type="authentication",
            event_action="login_success",
            user_name="finance_user",
        ),
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=30),
            event_type="authentication",
            event_action="login_failed",
            user_name="finance_user",
        ),
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=60),
            event_type="authentication",
            event_action="login_failed",
            user_name="finance_user",
        ),
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


# --------------------------------------------------------------------------
# Rule 3: Port Scan Unit Tests
# --------------------------------------------------------------------------

def test_rule3_port_scan_true_positive(test_log_source: LogSource):
    """5 distinct destination ports contacted on target within 60s triggers Rule 3."""
    rule = PortScanRule(threshold_count=5, time_window_seconds=60)
    base_time = datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc)

    ports = [22, 80, 443, 3389, 8080]
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 5),
            event_type="network",
            event_action="connection_attempt",
            source_ip="192.168.1.50",
            destination_ip="10.0.0.10",
            destination_port=port,
        )
        for i, port in enumerate(ports)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_code == "SEC-NET-001"
    assert f.evidence["distinct_ports_contacted"] == 5
    assert set(f.evidence["scanned_ports"]) == {22, 80, 443, 3389, 8080}
    assert len(f.supporting_event_ids) == 5


def test_rule3_port_scan_repeated_same_port_negative(test_log_source: LogSource):
    """5 connection attempts to the SAME port (e.g. HTTP 80) does NOT trigger port scan."""
    rule = PortScanRule(threshold_count=5, time_window_seconds=60)
    base_time = datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 5),
            event_type="network",
            event_action="allow",
            source_ip="192.168.1.50",
            destination_ip="10.0.0.10",
            destination_port=80,  # All to port 80
        )
        for i in range(5)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


def test_rule3_port_scan_below_threshold(test_log_source: LogSource):
    """4 distinct destination ports (below threshold of 5) does NOT trigger Rule 3."""
    rule = PortScanRule(threshold_count=5, time_window_seconds=60)
    base_time = datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc)

    ports = [22, 80, 443, 3389]
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 5),
            event_type="network",
            source_ip="192.168.1.50",
            destination_ip="10.0.0.10",
            destination_port=port,
        )
        for i, port in enumerate(ports)
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


# --------------------------------------------------------------------------
# Rule 4: Unusual Auth Patterns Unit Tests
# --------------------------------------------------------------------------

def test_rule4_multi_ip_velocity_true_positive(test_log_source: LogSource):
    """User accessed from 3 distinct IPs within 900s triggers Rule 4 velocity detection."""
    rule = UnusualAuthRule(multi_ip_threshold=3, velocity_window_seconds=900)
    base_time = datetime(2026, 3, 1, 15, 0, 0, tzinfo=timezone.utc)

    ips = ["10.1.1.1", "10.2.2.2", "10.3.3.3"]
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 60),
            event_type="authentication",
            event_action="login_success",
            source_ip=ip,
            user_name="bob",
        )
        for i, ip in enumerate(ips)
    ]

    findings = rule.evaluate(events)
    velocity_findings = [f for f in findings if f.evidence.get("pattern_type") == "multi_ip_velocity"]
    assert len(velocity_findings) == 1
    assert velocity_findings[0].evidence["distinct_ip_count"] == 3


def test_rule4_off_hours_privileged_login_true_positive(test_log_source: LogSource):
    """Admin login at 02:30 UTC triggers Rule 4 off-hours detection."""
    rule = UnusualAuthRule(off_hours_start_utc=0, off_hours_end_utc=5)
    off_hours_time = datetime(2026, 3, 1, 2, 30, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            off_hours_time,
            event_type="authentication",
            event_action="login_success",
            source_ip="192.168.1.200",
            user_name="admin",
        )
    ]

    findings = rule.evaluate(events)
    offhours_findings = [f for f in findings if f.evidence.get("pattern_type") == "off_hours_privileged_access"]
    assert len(offhours_findings) == 1
    assert offhours_findings[0].evidence["hour_utc"] == 2


def test_rule4_regular_hours_admin_login_negative(test_log_source: LogSource):
    """Admin login at 14:00 UTC (business hours) does NOT trigger off-hours detection."""
    rule = UnusualAuthRule(off_hours_start_utc=0, off_hours_end_utc=5)
    work_time = datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc)

    events = [
        make_event(
            test_log_source.id,
            work_time,
            event_type="authentication",
            event_action="login_success",
            source_ip="192.168.1.200",
            user_name="admin",
        )
    ]

    findings = rule.evaluate(events)
    assert len(findings) == 0


# --------------------------------------------------------------------------
# Detection Engine: Deduplication, Cooldown, and Error Handling
# --------------------------------------------------------------------------

def test_engine_alert_deduplication_and_cooldown(db_session: Session, test_log_source: LogSource):
    """Reprocessing the same events updates event_count instead of creating duplicate alerts."""
    engine = DetectionEngine()
    engine.sync_rules(db_session)

    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 10),
            event_type="authentication",
            event_action="login_failed",
            source_ip="203.0.113.15",
            user_name="targeted_user",
        )
        for i in range(5)
    ]

    # First evaluation pass
    alerts_pass1 = engine.evaluate_events(events, db_session)
    assert len(alerts_pass1) == 1
    alert_id = alerts_pass1[0].id
    assert alerts_pass1[0].event_count == 5

    # Second evaluation pass with same events
    alerts_pass2 = engine.evaluate_events(events, db_session)
    assert len(alerts_pass2) == 1
    assert alerts_pass2[0].id == alert_id  # Reused same alert record!
    assert alerts_pass2[0].event_count == 10  # Coalesced count

    # Confirm only one alert exists in database table
    total_db_alerts = db_session.query(SecurityAlert).count()
    assert total_db_alerts == 1


def test_engine_missing_fields_robustness(db_session: Session, test_log_source: LogSource):
    """Events with None for IP, username, or port evaluate cleanly without crashing."""
    engine = DetectionEngine()
    engine.sync_rules(db_session)

    sparse_events = [
        make_event(
            test_log_source.id,
            datetime.now(timezone.utc),
            event_type="authentication",
            event_action="login_failed",
            source_ip=None,
            destination_ip=None,
            user_name=None,
            destination_port=None,
        )
    ]

    # Must complete without unhandled exception
    alerts = engine.evaluate_events(sparse_events, db_session)
    assert isinstance(alerts, list)


def test_engine_error_isolation(db_session: Session, test_log_source: LogSource):
    """A crashing custom rule records error without halting engine or other rules."""
    class CrashingRule(BaseDetectionRule):
        rule_code = "SEC-FAIL-999"
        name = "Deliberately Broken Rule"
        description = "Simulates an unhandled exception inside a rule plugin"
        severity = RuleSeverity.LOW
        rule_type = RuleType.THRESHOLD

        def evaluate(self, events: List[NormalizedSecurityEvent], context: RuleContext = None):
            raise RuntimeError("Simulated runtime defect in rule logic")

    custom_registry = RuleRegistry()
    engine = DetectionEngine(registry=custom_registry)

    # Register crashing rule alongside valid rule
    engine.registry.register(CrashingRule())
    engine.registry.register(RepeatedFailedLoginsRule(threshold_count=5, time_window_seconds=300))

    engine.sync_rules(db_session)

    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 10),
            event_type="authentication",
            event_action="login_failed",
            source_ip="203.0.113.15",
            user_name="targeted_user",
        )
        for i in range(5)
    ]

    alerts = engine.evaluate_events(events, db_session)
    # The valid rule should still successfully produce an alert!
    assert len(alerts) == 1
    assert alerts[0].rule.rule_code == "SEC-AUTH-001"
    # Error was recorded in engine.last_errors
    assert len(engine.last_errors) == 1
    assert engine.last_errors[0]["rule_code"] == "SEC-FAIL-999"


# --------------------------------------------------------------------------
# Detection Rules & Alert Detail API Integration Tests
# --------------------------------------------------------------------------

def test_api_list_rules(client: TestClient):
    """GET /api/v1/rules returns documentation, assumptions, and MITRE tags."""
    resp = client.get("/api/v1/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) >= 4

    rule_codes = {r["rule_code"] for r in rules}
    assert "SEC-AUTH-001" in rule_codes
    assert "SEC-AUTH-002" in rule_codes
    assert "SEC-NET-001" in rule_codes
    assert "SEC-AUTH-003" in rule_codes

    # Check documentation attributes
    r1 = next(r for r in rules if r["rule_code"] == "SEC-AUTH-001")
    assert r1["mitre_tactic"] == "Credential Access"
    assert len(r1["assumptions"]) > 0
    assert len(r1["expected_false_positives"]) > 0


def test_api_patch_rule_tuning(client: TestClient):
    """PATCH /api/v1/rules/{code} updates rule thresholds."""
    resp = client.patch(
        "/api/v1/rules/SEC-AUTH-001",
        json={"threshold_count": 8, "time_window_seconds": 600},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["threshold_count"] == 8
    assert updated["time_window_seconds"] == 600


def test_api_alert_detail_with_supporting_events(
    client: TestClient,
    db_session: Session,
    test_log_source: LogSource,
):
    """GET /api/v1/alerts/{id} returns full evidence and supporting events."""
    engine = DetectionEngine()
    engine.sync_rules(db_session)

    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    events = [
        make_event(
            test_log_source.id,
            base_time + timedelta(seconds=i * 10),
            event_type="authentication",
            event_action="login_failed",
            source_ip="192.0.2.1",
            user_name="admin",
        )
        for i in range(5)
    ]
    db_session.add_all(events)
    db_session.commit()

    alerts = engine.evaluate_events(events, db_session)
    assert len(alerts) == 1
    alert_id = alerts[0].id

    resp = client.get(f"/api/v1/alerts/{alert_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(alert_id)
    assert len(data["supporting_events"]) == 5
    assert data["context_data"]["evidence"]["failed_attempts"] == 5


def test_api_alert_status_triage_update(
    client: TestClient,
    db_session: Session,
    test_log_source: LogSource,
):
    """PATCH /api/v1/alerts/{id}/status updates alert disposition."""
    engine = DetectionEngine()
    engine.sync_rules(db_session)

    events = [
        make_event(
            test_log_source.id,
            datetime.now(timezone.utc),
            event_type="authentication",
            event_action="login_failed",
            source_ip="192.0.2.1",
            user_name="admin",
        )
        for _ in range(5)
    ]
    db_session.add_all(events)
    db_session.commit()

    alerts = engine.evaluate_events(events, db_session)
    alert_id = alerts[0].id

    # Update status to triaged
    resp = client.patch(
        f"/api/v1/alerts/{alert_id}/status",
        json={"status": "triaged"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "triaged"


def test_api_replay_time_window(client: TestClient, db_session: Session):
    """POST /api/v1/rules/replay evaluates events within a window and reports metrics."""
    resp = client.post(
        "/api/v1/rules/replay",
        json={
            "start_time": "2026-03-01T00:00:00Z",
            "end_time": "2026-03-02T00:00:00Z",
        },
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "events_evaluated" in res
    assert "alerts_generated_or_updated" in res
