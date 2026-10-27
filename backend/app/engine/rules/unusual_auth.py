"""Rule SEC-AUTH-003: Unusual Authentication Patterns Detection."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from app.engine.base import BaseDetectionRule, DetectionResult, RuleContext
from app.models.event import NormalizedSecurityEvent
from app.models.rule import RuleSeverity, RuleType


class UnusualAuthRule(BaseDetectionRule):
    """Detects anomalous authentication patterns using transparent, deterministic criteria.

    Rather than relying on opaque machine learning claims, this rule evaluates two
    verifiable operational deviations:
    1. Multi-IP Velocity / Geographic Spray: The same user account successfully or
       unsuccessfully authenticates from 3 or more distinct source IP addresses
       within a 15-minute sliding window.
    2. Off-Hours Privileged Access: Successful authentication for high-privilege
       accounts (e.g. 'admin', 'root', 'administrator') during anomalous hours
       (between 00:00 and 05:00 UTC).
    """

    rule_code = "SEC-AUTH-003"
    name = "Unusual Authentication Pattern Deviation"
    description = (
        "Detects transparent authentication anomalies: multi-source IP velocity "
        "targeting a single account within a short window, or privileged off-hours authentication."
    )
    severity = RuleSeverity.MEDIUM
    rule_type = RuleType.ANOMALY
    mitre_tactic = "Initial Access"
    mitre_technique = "T1078 - Valid Accounts"
    time_window_seconds = 900  # 15 minutes for velocity checks
    threshold_count = 3  # At least 3 distinct IPs for velocity check
    remediation_guidance = (
        "1. For multi-IP velocity: Verify whether the user was using a VPN, cellular proxy, or travel connection.\n"
        "2. For off-hours privileged access: Confirm whether an active change window or emergency on-call ticket exists.\n"
        "3. Review multi-factor authentication (MFA) logs to ensure out-of-band challenge was validated.\n"
        "4. If unapproved, suspend active session and invoke emergency credential rotation."
    )

    assumptions = [
        "Authentication telemetry accurately captures the client source IP.",
        "System clocks record events normalized to UTC.",
        "Privileged roles or critical usernames can be identified by naming convention or policy.",
    ]
    limitations = [
        "Users accessing corporate infrastructure through load-balanced or rotating proxy pools may naturally show multi-IP velocity.",
        "Off-hours baseline is based on UTC; multinational remote teams may operate across differing local working hours.",
    ]
    expected_false_positives = [
        "Distributed scraping or synthetic health-check probes using cycling egress IP addresses.",
        "On-call infrastructure engineers responding to an overnight production alert between 00:00 and 05:00 UTC.",
        "Mobile phone users shifting between Wi-Fi and 5G cellular carriers.",
    ]

    DEFAULT_MONITORED_USERS = {
        "admin",
        "administrator",
        "root",
        "system",
        "service_account",
        "secops",
        "domain_admin",
    }

    def __init__(
        self,
        multi_ip_threshold: int = 3,
        velocity_window_seconds: int = 900,
        off_hours_start_utc: int = 0,
        off_hours_end_utc: int = 5,
        monitored_users: Optional[Set[str]] = None,
    ) -> None:
        self.threshold_count = multi_ip_threshold
        self.time_window_seconds = velocity_window_seconds
        self.off_hours_start_utc = off_hours_start_utc
        self.off_hours_end_utc = off_hours_end_utc
        self.monitored_users = monitored_users or self.DEFAULT_MONITORED_USERS

    def evaluate(
        self,
        events: List[NormalizedSecurityEvent],
        context: Optional[RuleContext] = None,
    ) -> List[DetectionResult]:
        """Evaluates authentication events for multi-IP velocity and off-hours access."""
        window_sec = context.time_window_seconds if context else self.time_window_seconds
        threshold = (
            context.custom_params.get("threshold_count", self.threshold_count)
            if context and context.custom_params
            else self.threshold_count
        )

        auth_events = [
            e for e in events if e.event_type == "authentication" and e.user_name
        ]
        if not auth_events:
            return []

        results: List[DetectionResult] = []

        # -------------------------------------------------------------
        # Criterion 1: Multi-IP Velocity (Same account from >= N distinct IPs)
        # -------------------------------------------------------------
        user_grouped: Dict[str, List[NormalizedSecurityEvent]] = defaultdict(list)
        for e in auth_events:
            user_clean = e.user_name.strip().lower()
            if e.source_ip:
                user_grouped[user_clean].append(e)

        for user, user_evs in user_grouped.items():
            sorted_evs = sorted(user_evs, key=lambda ev: ev.timestamp)
            n = len(sorted_evs)
            if n < threshold:
                continue

            i = 0
            while i < n:
                window_start = sorted_evs[i].timestamp
                window_evs = [
                    ev
                    for ev in sorted_evs[i:]
                    if (ev.timestamp - window_start).total_seconds() <= window_sec
                ]

                distinct_ips = {ev.source_ip for ev in window_evs if ev.source_ip}
                if len(distinct_ips) >= threshold:
                    # Representative supporting events (one per distinct IP)
                    supporting: List[NormalizedSecurityEvent] = []
                    seen_ips = set()
                    for ev in window_evs:
                        if ev.source_ip not in seen_ips:
                            seen_ips.add(ev.source_ip)
                            supporting.append(ev)

                    last_ev = window_evs[-1]
                    hour_bucket = last_ev.timestamp.strftime("%Y%m%d%H")
                    dedup_key = f"{self.rule_code}:velocity:{user}:{hour_bucket}"

                    evidence: Dict[str, Any] = {
                        "pattern_type": "multi_ip_velocity",
                        "user_name": user,
                        "distinct_ip_count": len(distinct_ips),
                        "source_ips": sorted(list(distinct_ips)),
                        "threshold": threshold,
                        "time_window_seconds": window_sec,
                        "first_seen": window_evs[0].timestamp.isoformat(),
                        "last_seen": last_ev.timestamp.isoformat(),
                    }

                    results.append(
                        DetectionResult(
                            rule_code=self.rule_code,
                            title=f"Multi-IP Velocity: {user} ({len(distinct_ips)} distinct IPs)",
                            description=(
                                f"Account '{user}' was accessed from {len(distinct_ips)} distinct source IPs "
                                f"within {window_sec}s, exceeding anomaly threshold of {threshold}. "
                                f"Source IPs: {', '.join(sorted(list(distinct_ips)))}."
                            ),
                            severity=self.severity,
                            deduplication_key=dedup_key,
                            affected_entities={
                                "user_name": user,
                                "source_ips": sorted(list(distinct_ips)),
                            },
                            supporting_event_ids=[ev.id for ev in supporting],
                            evidence=evidence,
                        )
                    )
                    i += len(window_evs)
                else:
                    i += 1

        # -------------------------------------------------------------
        # Criterion 2: Off-Hours Privileged Access (00:00 - 05:00 UTC)
        # -------------------------------------------------------------
        for e in auth_events:
            action = (e.event_action or "").lower()
            is_success = action in (
                "login_success",
                "success",
                "successful",
                "logon_success",
                "auth_success",
            )
            if not is_success:
                continue

            user_clean = e.user_name.strip().lower()
            if user_clean in self.monitored_users or "admin" in user_clean:
                hour = e.timestamp.hour
                if self.off_hours_start_utc <= hour < self.off_hours_end_utc:
                    day_bucket = e.timestamp.strftime("%Y%m%d")
                    dedup_key = f"{self.rule_code}:offhours:{user_clean}:{day_bucket}"

                    evidence_offhours: Dict[str, Any] = {
                        "pattern_type": "off_hours_privileged_access",
                        "user_name": user_clean,
                        "login_timestamp": e.timestamp.isoformat(),
                        "source_ip": e.source_ip,
                        "hour_utc": hour,
                        "off_hours_window_utc": f"{self.off_hours_start_utc:02d}:00 - {self.off_hours_end_utc:02d}:00 UTC",
                    }

                    results.append(
                        DetectionResult(
                            rule_code=self.rule_code,
                            title=f"Off-Hours Privileged Login: {user_clean} at {hour:02d}:00 UTC",
                            description=(
                                f"Privileged account '{user_clean}' successfully authenticated at "
                                f"{e.timestamp.isoformat()} (UTC Hour {hour:02d}), falling within the monitored "
                                f"off-hours window ({self.off_hours_start_utc:02d}:00 - {self.off_hours_end_utc:02d}:00 UTC). "
                                f"Source IP: {e.source_ip or 'unknown'}."
                            ),
                            severity=RuleSeverity.MEDIUM,
                            deduplication_key=dedup_key,
                            affected_entities={
                                "user_name": user_clean,
                                "source_ip": e.source_ip,
                            },
                            supporting_event_ids=[e.id],
                            evidence=evidence_offhours,
                        )
                    )

        return results
