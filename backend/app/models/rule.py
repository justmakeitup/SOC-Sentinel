"""Detection rule definitions mapping MITRE ATT&CK techniques to telemetry logic."""

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyUUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import SecurityAlert
    from app.models.user import User


class RuleSeverity(str, enum.Enum):
    """Detection severity defining default response SLA."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleType(str, enum.Enum):
    """Execution model for the detection condition."""
    THRESHOLD = "threshold"          # e.g., > N events matching criteria within T seconds
    SQL_MATCH = "sql_match"          # Direct parameter evaluation or regex match
    CORRELATION = "correlation"      # Multi-event sequential pattern
    ANOMALY = "anomaly"              # Statistical deviation from baseline


class DetectionRule(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    """Rule evaluated by the Sentinel detection engine against normalized event streams."""

    __tablename__ = "detection_rules"

    rule_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
        doc="Structured rule mnemonic (e.g., 'SEC-BRUTE-001', 'SEC-RANSOM-012')",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Concise human-readable description of detected activity",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed rationale, threat landscape context, and triage triage guidelines",
    )
    severity: Mapped[RuleSeverity] = mapped_column(
        Enum(RuleSeverity, name="rule_severity_enum", native_enum=False),
        default=RuleSeverity.MEDIUM,
        nullable=False,
        index=True,
    )
    rule_type: Mapped[RuleType] = mapped_column(
        Enum(RuleType, name="rule_type_enum", native_enum=False),
        default=RuleType.THRESHOLD,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Controls whether the detection engine evaluates this rule",
    )
    time_window_seconds: Mapped[int] = mapped_column(
        Integer,
        default=300,
        nullable=False,
        doc="Sliding window duration in seconds for aggregation queries",
    )
    threshold_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Number of matching occurrences required to trigger an alert",
    )

    # MITRE ATT&CK Framework Tagging
    mitre_tactic: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="MITRE Enterprise ATT&CK Tactic (e.g., 'Credential Access', 'Defense Evasion')",
    )
    mitre_technique: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="MITRE Technique ID (e.g., 'T1110.001 - Password Guessing')",
    )

    # Structured detection logic definition
    rule_logic: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Structured conditions: filters (event_type, action, ports), grouping keys, thresholds",
    )
    remediation_guidance: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Prescriptive runbook instructions for Tier-1 analysts responding to this alert",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Revision number incremented on modification for detection engineering change control",
    )

    # Authorship
    created_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Detection engineer responsible for rule creation",
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_rules",
    )
    alerts: Mapped[List["SecurityAlert"]] = relationship(
        "SecurityAlert",
        back_populates="rule",
    )

    def __repr__(self) -> str:
        return f"<DetectionRule {self.rule_code}: {self.name} (active={self.is_active})>"
