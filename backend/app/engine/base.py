"""Base interfaces and data structures for the Sentinel detection engine."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.event import NormalizedSecurityEvent
from app.models.rule import RuleSeverity, RuleType


@dataclass
class RuleContext:
    """Execution context provided to rules during evaluation."""

    evaluation_time: datetime
    time_window_seconds: int = 300
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionResult:
    """Structured security alert candidate produced by a detection rule."""

    rule_code: str
    title: str
    description: str
    severity: RuleSeverity
    deduplication_key: str
    affected_entities: Dict[str, Any]
    supporting_event_ids: List[UUID]
    evidence: Dict[str, Any]


class BaseDetectionRule(ABC):
    """Abstract interface for all transparent, rule-based detection plugins."""

    rule_code: str
    name: str
    description: str
    severity: RuleSeverity
    rule_type: RuleType
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    time_window_seconds: int = 300
    threshold_count: int = 1
    remediation_guidance: Optional[str] = None

    # Transparent documentation of rationale, assumptions, and false positives
    assumptions: List[str] = []
    limitations: List[str] = []
    expected_false_positives: List[str] = []

    def get_documentation(self) -> Dict[str, Any]:
        """Returns structured metadata explaining the rule rationale and triage guidance."""
        return {
            "rule_code": self.rule_code,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "rule_type": self.rule_type.value,
            "mitre_tactic": self.mitre_tactic,
            "mitre_technique": self.mitre_technique,
            "time_window_seconds": self.time_window_seconds,
            "threshold_count": self.threshold_count,
            "remediation_guidance": self.remediation_guidance,
            "assumptions": self.assumptions,
            "limitations": self.limitations,
            "expected_false_positives": self.expected_false_positives,
        }

    @abstractmethod
    def evaluate(
        self,
        events: List[NormalizedSecurityEvent],
        context: Optional[RuleContext] = None,
    ) -> List[DetectionResult]:
        """Evaluates a collection of normalized security events against rule criteria."""
        pass
