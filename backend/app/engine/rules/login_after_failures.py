"""Rule SEC-AUTH-002: Successful Login Following Repeated Failures Correlation."""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.engine.base import BaseDetectionRule, DetectionResult, RuleContext
from app.models.event import NormalizedSecurityEvent
from app.models.rule import RuleSeverity, RuleType


class LoginAfterFailuresRule(BaseDetectionRule):
    """Correlates multiple failed logins followed by a successful login.

    Without assuming malicious intent, this rule surfaces sequences where an
    account experienced multiple failed attempts before a successful logon. This may
    indicate a password guessing attack, credential stuffing, or simply an authorized
    user struggling with credential entry (e.g., Caps Lock).
    """

    rule_code = "SEC-AUTH-002"
    name = "Successful Login Following Repeated Failures"
    description = (
        "Identifies a successful authentication event preceded by multiple failed "
        "login attempts for the same account within a configured correlation window."
    )
    severity = RuleSeverity.MEDIUM
    rule_type = RuleType.CORRELATION
    mitre_tactic = "Credential Access"
    mitre_technique = "T1110.001 - Password Guessing"
    time_window_seconds = 600  # 10-minute correlation window
    threshold_count = 3  # Minimum 3 failures preceding the success
    remediation_guidance = (
        "1. Compare the source IP of the failed attempts with the source IP of the successful login.\n"
        "2. If the IPs differ, investigate whether an attacker obtained valid credentials via brute-force.\n"
        "3. Inspect post-login user activity (e.g. privilege escalation, unusual data queries).\n"
        "4. Contact the account owner to verify whether the failures were due to mistyped passwords."
    )

    assumptions = [
        "Authentication logs record both failed and successful login events.",
        "Timestamps reliably preserve causal chronological ordering between failure and success.",
    ]
    limitations = [
        "If authentication failure logs and success logs arrive through disparate channels with large ingestion lag, real-time correlation may be delayed.",
        "Cannot distinguish in isolation between a user who forgot their password vs. an adversary who guessed it without context.",
    ]
    expected_false_positives = [
        "Legitimate employees who mistype their password multiple times before entering the correct one.",
        "Users recovering from an accidental Caps Lock key activation.",
    ]

    def __init__(
        self,
        threshold_count: int = 3,
        time_window_seconds: int = 600,
    ) -> None:
        self.threshold_count = threshold_count
        self.time_window_seconds = time_window_seconds

    def evaluate(
        self,
        events: List[NormalizedSecurityEvent],
        context: Optional[RuleContext] = None,
    ) -> List[DetectionResult]:
        """Correlates failure sequences followed chronologically by a success."""
        window_sec = context.time_window_seconds if context else self.time_window_seconds
        threshold = (
            context.custom_params.get("threshold_count", self.threshold_count)
            if context and context.custom_params
            else self.threshold_count
        )

        # 1. Filter authentication events
        auth_events = [e for e in events if e.event_type == "authentication"]
        if not auth_events:
            return []

        # 2. Group events by user_name
        grouped_by_user: Dict[str, List[NormalizedSecurityEvent]] = defaultdict(list)
        for e in auth_events:
            user = (e.user_name or "unknown").strip().lower()
            if user != "unknown":
                grouped_by_user[user].append(e)

        results: List[DetectionResult] = []

        # 3. For each user, walk chronological sequence
        for user, user_events in grouped_by_user.items():
            sorted_events = sorted(user_events, key=lambda ev: ev.timestamp)
            recent_failures: List[NormalizedSecurityEvent] = []

            for ev in sorted_events:
                action = (ev.event_action or "").lower()
                is_failure = action in (
                    "login_failed",
                    "failure",
                    "failed",
                    "logon_failed",
                    "auth_failed",
                )
                is_success = action in (
                    "login_success",
                    "success",
                    "successful",
                    "logon_success",
                    "auth_success",
                )

                if is_failure:
                    recent_failures.append(ev)
                elif is_success:
                    # Filter failures that occurred strictly before this success and within correlation window
                    valid_prior_failures = [
                        fail
                        for fail in recent_failures
                        if 0 < (ev.timestamp - fail.timestamp).total_seconds() <= window_sec
                    ]

                    if len(valid_prior_failures) >= threshold:
                        hour_bucket = ev.timestamp.strftime("%Y%m%d%H")
                        dedup_key = f"{self.rule_code}:{user}:{hour_bucket}"
                        failure_ips = list(
                            set(f.source_ip for f in valid_prior_failures if f.source_ip)
                        )
                        supporting_ids = [f.id for f in valid_prior_failures] + [ev.id]

                        evidence: Dict[str, Any] = {
                            "preceding_failed_count": len(valid_prior_failures),
                            "threshold": threshold,
                            "correlation_window_seconds": window_sec,
                            "user_name": user,
                            "success_timestamp": ev.timestamp.isoformat(),
                            "success_source_ip": ev.source_ip,
                            "failure_source_ips": failure_ips,
                            "first_failure_timestamp": valid_prior_failures[0].timestamp.isoformat(),
                        }

                        results.append(
                            DetectionResult(
                                rule_code=self.rule_code,
                                title=f"Successful Login Following {len(valid_prior_failures)} Failures: {user}",
                                description=(
                                    f"User '{user}' successfully authenticated at {ev.timestamp.isoformat()} "
                                    f"after {len(valid_prior_failures)} failed attempts within {window_sec}s. "
                                    f"Success IP: {ev.source_ip or 'unknown'}."
                                ),
                                severity=self.severity,
                                deduplication_key=dedup_key,
                                affected_entities={
                                    "user_name": user,
                                    "source_ip": ev.source_ip,
                                },
                                supporting_event_ids=supporting_ids,
                                evidence=evidence,
                            )
                        )
                        # Reset failures to prevent duplicate firing on immediate next success
                        recent_failures = []
                    else:
                        # Prune failures that are older than window_sec relative to current event
                        recent_failures = [
                            f
                            for f in recent_failures
                            if (ev.timestamp - f.timestamp).total_seconds() <= window_sec
                        ]

        return results
