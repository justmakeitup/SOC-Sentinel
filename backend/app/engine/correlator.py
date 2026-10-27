"""Detection Engine: Event evaluation, rule synchronization, and alert correlation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.engine.base import DetectionResult, RuleContext
from app.engine.registry import RuleRegistry, default_registry
from app.engine.rules import (
    LoginAfterFailuresRule,
    PortScanRule,
    RepeatedFailedLoginsRule,
    UnusualAuthRule,
)
from app.models.alert import AlertStatus, SecurityAlert
from app.models.event import NormalizedSecurityEvent
from app.models.rule import DetectionRule

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Core detection engine orchestrating rule execution, deduplication, and alert generation."""

    def __init__(self, registry: Optional[RuleRegistry] = None) -> None:
        self.registry = registry or default_registry
        self.last_errors: List[Dict[str, Any]] = []
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Initializes default built-in detection rules."""
        if not self.registry.get("SEC-AUTH-001"):
            self.registry.register(RepeatedFailedLoginsRule())
        if not self.registry.get("SEC-AUTH-002"):
            self.registry.register(LoginAfterFailuresRule())
        if not self.registry.get("SEC-NET-001"):
            self.registry.register(PortScanRule())
        if not self.registry.get("SEC-AUTH-003"):
            self.registry.register(UnusualAuthRule())

    def sync_rules(self, db: Session) -> Dict[str, DetectionRule]:
        """Ensures all code-defined detection rules exist in the PostgreSQL detection_rules table."""
        existing_rules = {r.rule_code: r for r in db.query(DetectionRule).all()}
        synced: Dict[str, DetectionRule] = {}

        for rule in self.registry.get_all():
            if rule.rule_code not in existing_rules:
                db_rule = DetectionRule(
                    rule_code=rule.rule_code,
                    name=rule.name,
                    description=rule.description,
                    severity=rule.severity,
                    rule_type=rule.rule_type,
                    is_active=True,
                    time_window_seconds=rule.time_window_seconds,
                    threshold_count=rule.threshold_count,
                    mitre_tactic=rule.mitre_tactic,
                    mitre_technique=rule.mitre_technique,
                    remediation_guidance=rule.remediation_guidance,
                    rule_logic={
                        "assumptions": rule.assumptions,
                        "limitations": rule.limitations,
                        "expected_false_positives": rule.expected_false_positives,
                    },
                    version=1,
                )
                db.add(db_rule)
                db.flush()
                synced[rule.rule_code] = db_rule
                logger.info("Synchronized new detection rule to database: %s", rule.rule_code)
            else:
                synced[rule.rule_code] = existing_rules[rule.rule_code]

        db.commit()
        return synced

    def evaluate_events(
        self,
        events: List[NormalizedSecurityEvent],
        db: Session,
        context: Optional[RuleContext] = None,
    ) -> List[SecurityAlert]:
        """Evaluates normalized events against all active detection rules with error isolation."""
        if not events:
            return []

        # 1. Sync rules and load active rules from DB
        synced_rules = self.sync_rules(db)
        active_db_rules = [
            r for r in synced_rules.values() if r.is_active
        ]

        self.last_errors = []
        raw_candidates: List[DetectionResult] = []

        now = datetime.now(timezone.utc)

        # 2. Evaluate each rule in isolation (safe boundary)
        for db_rule in active_db_rules:
            rule_plugin = self.registry.get(db_rule.rule_code)
            if not rule_plugin:
                continue

            rule_ctx = RuleContext(
                evaluation_time=now,
                time_window_seconds=db_rule.time_window_seconds,
                custom_params={"threshold_count": db_rule.threshold_count},
            )

            try:
                findings = rule_plugin.evaluate(events, context=rule_ctx)
                if findings:
                    raw_candidates.extend(findings)
            except Exception as e:
                # Capture error without breaking pipeline
                err_detail = {
                    "rule_code": db_rule.rule_code,
                    "error": str(e),
                    "timestamp": now.isoformat(),
                }
                logger.exception("Error evaluating rule %s: %s", db_rule.rule_code, e)
                self.last_errors.append(err_detail)

        if not raw_candidates:
            return []

        # 3. Deduplicate and correlate candidates against existing alerts
        processed_alerts: List[SecurityAlert] = []

        for candidate in raw_candidates:
            db_rule = synced_rules.get(candidate.rule_code)
            if not db_rule:
                continue

            # Check if an active (unresolved) alert exists with same deduplication key
            existing_alert = (
                db.query(SecurityAlert)
                .filter(
                    SecurityAlert.deduplication_key == candidate.deduplication_key,
                    SecurityAlert.status.in_([
                        AlertStatus.NEW,
                        AlertStatus.TRIAGED,
                        AlertStatus.INVESTIGATING,
                    ]),
                )
                .order_by(SecurityAlert.created_at.desc())
                .first()
            )

            new_supporting_ids = [str(uid) for uid in candidate.supporting_event_ids]

            if existing_alert:
                # Update existing alert (suppression / cooldown window increment)
                existing_alert.event_count += max(len(candidate.supporting_event_ids), 1)

                ctx = dict(existing_alert.context_data or {})
                prior_ids = ctx.get("supporting_event_ids", [])
                # Combine unique IDs preserving order
                combined_ids = list(dict.fromkeys(prior_ids + new_supporting_ids))
                ctx["supporting_event_ids"] = combined_ids
                ctx["evidence"] = candidate.evidence
                ctx["last_updated_by_detection"] = now.isoformat()

                existing_alert.context_data = ctx
                existing_alert.updated_at = now
                processed_alerts.append(existing_alert)
            else:
                # Provision new Security Alert
                new_alert = SecurityAlert(
                    rule_id=db_rule.id,
                    title=candidate.title,
                    description=candidate.description,
                    severity=candidate.severity,
                    status=AlertStatus.NEW,
                    deduplication_key=candidate.deduplication_key,
                    event_count=max(len(candidate.supporting_event_ids), 1),
                    context_data={
                        "rule_code": candidate.rule_code,
                        "rule_name": db_rule.name,
                        "mitre_tactic": db_rule.mitre_tactic,
                        "mitre_technique": db_rule.mitre_technique,
                        "affected_entities": candidate.affected_entities,
                        "evidence": candidate.evidence,
                        "supporting_event_ids": new_supporting_ids,
                    },
                )
                db.add(new_alert)
                processed_alerts.append(new_alert)

        db.commit()

        for a in processed_alerts:
            db.refresh(a)

        return processed_alerts

    def replay_time_window(
        self,
        start_time: datetime,
        end_time: datetime,
        db: Session,
    ) -> Dict[str, Any]:
        """Replays synthetic or historical events within a timestamp range."""
        events = (
            db.query(NormalizedSecurityEvent)
            .filter(
                NormalizedSecurityEvent.timestamp >= start_time,
                NormalizedSecurityEvent.timestamp <= end_time,
            )
            .order_by(NormalizedSecurityEvent.timestamp.asc())
            .all()
        )

        alerts = self.evaluate_events(events, db)
        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "events_evaluated": len(events),
            "alerts_generated_or_updated": len(alerts),
            "errors": self.last_errors,
        }


default_engine = DetectionEngine()
