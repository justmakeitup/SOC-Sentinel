"""Log source definition and telemetry ingestion execution jobs."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyUUIDMixin, TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.event import NormalizedSecurityEvent


class LogSourceType(str, enum.Enum):
    """Supported telemetry telemetry formats and sensor collectors."""
    SYSLOG = "syslog"
    WINDOWS_EVENT_LOG = "windows_event_log"
    AUDITD = "auditd"
    ZEEK_NETWORK = "zeek_network"
    SURICATA_NIDS = "suricata_nids"
    CLOUDTRAIL = "cloudtrail"
    KUBERNETES = "kubernetes"
    APPLICATION_JSON = "application_json"
    CUSTOM = "custom"


class LogSourceStatus(str, enum.Enum):
    """Operational health state of the log emitter/sensor."""
    ACTIVE = "active"
    DEGRADED = "degraded"
    INACTIVE = "inactive"
    ERROR = "error"


class IngestionJobStatus(str, enum.Enum):
    """Execution lifecycle status of an ingestion pipeline run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_FAILED = "partially_failed"


class LogSource(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    """Configured network sensor, host agent, or cloud feed emitting security logs."""

    __tablename__ = "log_sources"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="Human-friendly label identifying the log collector (e.g., 'FW-Core-Primary')",
    )
    source_type: Mapped[LogSourceType] = mapped_column(
        Enum(LogSourceType, name="log_source_type_enum", native_enum=False),
        nullable=False,
        index=True,
        doc="Ingestion parser protocol/format specification",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Context regarding sensor location, subnet, and business criticality",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # Accommodates IPv4 and IPv6 representations
        nullable=True,
        doc="Network origin IP of collector or forwarder",
    )
    hostname: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="FQDN or hostname of collector host",
    )
    status: Mapped[LogSourceStatus] = mapped_column(
        Enum(LogSourceStatus, name="log_source_status_enum", native_enum=False),
        default=LogSourceStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    retention_days: Mapped[int] = mapped_column(
        Integer,
        default=90,
        nullable=False,
        doc="Number of days normalized logs from this source must be preserved",
    )
    config_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Parser regex, JSON mappings, port bindings, and custom extraction tags",
    )

    # Relationships
    ingestion_jobs: Mapped[List["IngestionJob"]] = relationship(
        "IngestionJob",
        back_populates="log_source",
        cascade="all, delete-orphan",
        order_by="desc(IngestionJob.started_at)",
    )
    security_events: Mapped[List["NormalizedSecurityEvent"]] = relationship(
        "NormalizedSecurityEvent",
        back_populates="log_source",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LogSource {self.name} (type={self.source_type}, status={self.status})>"


class IngestionJob(Base, PrimaryKeyUUIDMixin):
    """Audit record and execution metric for an automated or scheduled log ingestion run."""

    __tablename__ = "ingestion_jobs"

    log_source_id: Mapped[str] = mapped_column(
        ForeignKey("log_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the owning log source",
    )
    status: Mapped[IngestionJobStatus] = mapped_column(
        Enum(IngestionJobStatus, name="ingestion_job_status_enum", native_enum=False),
        default=IngestionJobStatus.PENDING,
        nullable=False,
        index=True,
    )
    batch_identifier: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        doc="Unique fingerprint or filename/chunk hash preventing duplicate batch ingestion",
    )
    events_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of events parsed and normalized successfully",
    )
    events_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of malformed records dropped or sent to dead-letter queue",
    )
    bytes_ingested: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
        doc="Raw byte volume consumed during this job",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Traceback or descriptive reason in case of pipeline failure",
    )
    rejected_records: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        doc="Detailed summaries of malformed rows with line numbers and validation reasons",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    log_source: Mapped["LogSource"] = relationship(
        "LogSource",
        back_populates="ingestion_jobs",
    )

    def __repr__(self) -> str:
        return f"<IngestionJob {self.id} for Source {self.log_source_id} (status={self.status})>"
