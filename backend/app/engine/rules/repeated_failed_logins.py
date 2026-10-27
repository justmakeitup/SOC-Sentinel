"""Rule SEC-AUTH-001: Repeated Failed Logins Detection."""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.engine.base import BaseDetectionRule, DetectionResult, RuleContext
from app.models.event import NormalizedSecurityEvent
from app.models.rule import RuleSeverity, RuleType


class RepeatedFailedLoginsRule(BaseDetectionRule):
    """Detects excessive failed authentication attempts within a sliding time window.

    This rule identifies automated password spraying, credential brute-forcing,
    or compromised automation attempting to authenticate repeatedly with bad credentials.
    """

    rule_code = "SEC-AUTH-001"
    name = "Repeated Failed Authentication Attempts"
    description = (
        "Detects a high volume of failed authentication events targeting an account or "
        "originating from a single host within a configurable time window."
    )
    severity = RuleSeverity.HIGH
    rule_type = RuleType.THRESHOLD
    mitre_tactic = "Credential Access"
    mitre_technique = "T1110 - Brute Force"
    time_window_seconds = 300  # 5-minute sliding window
    threshold_count = 5  # At least 5 failed logins
    remediation_guidance = (
        "1. Identify whether the affected username is an interactive user or service account.\n"
        "2. Check source IP reputation and internal subnet ownership.\n"
        "3. Review whether a successful login occurred immediately following these failures.\n"
        "4. Temporarily restrict source IP at perimeter firewall or initiate password reset if targeted."
    )

    assumptions = [
        "Authentication data sources reliably emit 'login_failed', 'failure', or 'failed' actions.",
        "Timestamps reflect UTC event generation accurately within telemetry latency bounds.",
    ]
    limitations = [
        "Slow-and-low brute force attacks (e.g. 1 attempt every 10 minutes) stay below the sliding window.",
        "Distributed attacks rotating across hundreds of unique IPs may evade single-IP grouping.",
    ]
    expected_false_positives = [
        "Users with recently expired enterprise passwords whose mobile devices or Outlook clients retry automatically.",
        "Misconfigured service accounts or scheduled Cron jobs attempting connections with stale API tokens.",
    ]

    def __init__(
        self,
        threshold_count: int = 5,
        time_window_seconds: int = 300,
    ) -> None:
        self.threshold_count = threshold_count
        self.time_window_seconds = time_window_seconds

    def evaluate(
        self,
        events: List[NormalizedSecurityEvent],
        context: Optional[RuleContext] = None,
    ) -> List[DetectionResult]:
        """Evaluates events against failed login threshold within a sliding window."""
        window_sec = context.time_window_seconds if context else self.time_window_seconds
        threshold = (
            context.custom_params.get("threshold_count", self.threshold_count)
            if context and context.custom_params
            else self.threshold_count
        )

        # 1. Filter relevant authentication failure events
        matching_events = [
            e
            for e in events
            if e.event_type == "authentication"
            and (e.event_action or "").lower() in (
                "login_failed",
                "failure",
                "failed",
                "logon_failed",
                "auth_failed",
            )
        ]

        if not matching_events:
            return []

        # 2. Group events by primary entity pair (user_name, source_ip)
        # Using normalized fallback if one entity is omitted
        grouped: Dict[tuple, List[NormalizedSecurityEvent]] = defaultdict(list)
        for e in matching_events:
            user = (e.user_name or "unknown").strip().lower()
            ip = (e.source_ip or "unknown").strip()
            grouped[(user, ip)].append(e)

        results: List[DetectionResult] = []

        # 3. For each entity group, evaluate sliding temporal windows
        for (user, ip), entity_events in grouped.items():
            # Sort chronologically
            sorted_events = sorted(entity_events, key=lambda ev: ev.timestamp)
            n = len(sorted_events)
            if n < threshold:
                continue

            i = 0
            while i < n:
                window_start = sorted_events[i].timestamp
                # Find all events falling within [window_start, window_start + window_sec]
                window_events = [
                    ev
                    for ev in sorted_events[i:]
                    if (ev.timestamp - window_start).total_seconds() <= window_sec
                ]

                if len(window_events) >= threshold:
                    # Construct candidate alert
                    first_ev = window_events[0]
                    last_ev = window_events[-1]
                    hour_bucket = last_ev.timestamp.strftime("%Y%m%d%H")
                    dedup_key = f"{self.rule_code}:{user}:{ip}:{hour_bucket}"

                    evidence: Dict[str, Any] = {
                        "failed_attempts": len(window_events),
                        "threshold": threshold,
                        "time_window_seconds": window_sec,
                        "user_name": user,
                        "source_ip": ip,
                        "first_seen": first_ev.timestamp.isoformat(),
                        "last_seen": last_ev.timestamp.isoformat(),
                    }

                    results.append(
                        DetectionResult(
                            rule_code=self.rule_code,
                            title=f"Excessive Failed Logins: {user} ({len(window_events)} attempts from {ip})",
                            description=(
                                f"Observed {len(window_events)} consecutive failed authentication attempts "
                                f"for user '{user}' from source IP '{ip}' within {window_sec}s, "
                                f"exceeding threshold of {threshold}."
                            ),
                            severity=self.severity,
                            deduplication_key=dedup_key,
                            affected_entities={
                                "user_name": user if user != "unknown" else None,
                                "source_ip": ip if ip != "unknown" else None,
                            },
                            supporting_event_ids=[ev.id for ev in window_events],
                            evidence=evidence,
                        )
                    )

                    # Advance index past this window to avoid duplicate alert spam in same batch
                    i += len(window_events)
                else:
                    i += 1

        return results
