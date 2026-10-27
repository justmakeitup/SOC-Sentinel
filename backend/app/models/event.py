"""Normalized security telemetry model following unified SOC taxonomies."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyUUIDMixin, utc_now

if TYPE_CHECKING:
    from app.models.log_source import LogSource


class EventSeverity(str, enum.Enum):
    """Base severity rating for individual normalized events."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NormalizedSecurityEvent(Base, PrimaryKeyUUIDMixin):
    """Normalized security telemetry event structured for detection evaluation and hunting.

    Fields harmonize disparate telemetry formats (Syslog, Windows Event Logs, Zeek,
    CloudTrail) into a consistent schema based on standard security event models (ECS/OSSEM).
    Deduplication is enforced cryptographically through the unique `event_hash`.
    """

    __tablename__ = "normalized_security_events"

    log_source_id: Mapped[str] = mapped_column(
        ForeignKey("log_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Originating sensor or collector",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Actual point in time when the event occurred on the remote endpoint/device",
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Point in time when Sentinel pipeline received and indexed the event",
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Categorical classification (e.g., authentication, network_flow, process_exec)",
    )
    event_action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Specific operational verb (e.g., login_failed, connection_denied, user_created)",
    )
    severity: Mapped[EventSeverity] = mapped_column(
        Enum(EventSeverity, name="event_severity_enum", native_enum=False),
        default=EventSeverity.INFORMATIONAL,
        nullable=False,
        index=True,
    )

    # Network Telemetry
    source_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        doc="Origin IPv4/IPv6 address",
    )
    source_port: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    destination_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        doc="Target IPv4/IPv6 address",
    )
    destination_port: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    protocol: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        doc="Layer 4 / Layer 7 protocol (e.g., TCP, UDP, TLS, DNS, SSH)",
    )

    # Host & Identity Telemetry
    user_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        doc="Subject user account or Kerberos principal associated with the activity",
    )
    host_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="FQDN or NetBIOS machine name where activity transpired",
    )
    process_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Binary image name (e.g., powershell.exe, sshd)",
    )
    process_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    command_line: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Executed command string with parameters/arguments for behavioral inspection",
    )

    # Raw Payload & Cryptographic Deduplication
    raw_payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Immutable raw log line string retained for forensic chain-of-custody",
    )
    event_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 fingerprint (source_id + timestamp + raw_payload) guaranteeing idempotent ingestion",
    )
    extra_fields: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Dialect-specific auxiliary fields, HTTP headers, or TLS cipher suites",
    )

    # Relationships
    log_source: Mapped["LogSource"] = relationship(
        "LogSource",
        back_populates="security_events",
    )

    __table_args__ = (
        Index("idx_events_source_time", "log_source_id", "timestamp"),
        Index("idx_events_type_time", "event_type", "timestamp"),
        Index("idx_events_src_ip_time", "source_ip", "timestamp"),
        Index("idx_events_dst_ip_time", "destination_ip", "timestamp"),
        UniqueConstraint("event_hash", name="uq_event_hash_deduplication"),
    )

    def __repr__(self) -> str:
        return f"<NormalizedEvent {self.id} type={self.event_type} action={self.event_action} time={self.timestamp}>"
