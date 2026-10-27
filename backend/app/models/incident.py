"""Incident response case management and chronological analyst investigation notes."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyUUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import SecurityAlert
    from app.models.user import User


class IncidentSeverity(str, enum.Enum):
    """Standardized NIST SP 800-61 incident impact rating."""
    SEV_1_CRITICAL = "sev_1_critical"  # Enterprise-wide impact, active data exfiltration
    SEV_2_HIGH = "sev_2_high"          # Critical system compromise or lateral movement
    SEV_3_MEDIUM = "sev_3_medium"      # Isolated malware or contained unauthorized access
    SEV_4_LOW = "sev_4_low"            # Minor policy violation or low-risk suspicious finding


class IncidentStatus(str, enum.Enum):
    """Incident handling lifecycle phases aligned with NIST SP 800-61 Rev 2."""
    OPEN = "open"                                  # Initial escalation and scope verification
    CONTAINMENT = "containment"                    # Short/long-term containment measures applied
    ERADICATION = "eradication"                    # Root cause and persistence mechanisms removed
    RECOVERY = "recovery"                          # Restoring systems to clean production operations
    POST_INCIDENT_REVIEW = "post_incident_review"  # Lessons learned and timeline retrospective
    CLOSED = "closed"                              # Incident officially concluded


class NoteType(str, enum.Enum):
    """Classification of forensic investigation documentation."""
    ANALYSIS = "analysis"
    CONTAINMENT_ACTION = "containment_action"
    FORENSIC_EVIDENCE = "forensic_evidence"
    COMMUNICATION = "communication"
    GENERAL = "general"


class Incident(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    """Incident response investigation file bundling related alerts and forensic findings."""

    __tablename__ = "incidents"

    incident_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
        doc="Formatted reference identifier (e.g., 'INC-2026-0001')",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Incident title summarizing the threat actor or vector",
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Executive narrative of the security incident and impact",
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity_enum", native_enum=False),
        default=IncidentSeverity.SEV_3_MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status_enum", native_enum=False),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True,
    )
    lead_analyst_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Incident Commander or Lead Investigator responsible for case resolution",
    )
    containment_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Chronicle of network isolations, token revocations, and firewall blocks",
    )
    lessons_learned: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Post-mortem action items to prevent recurrence",
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when case was formally marked closed",
    )

    # Relationships
    lead_analyst: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="lead_incidents",
    )
    alerts: Mapped[List["SecurityAlert"]] = relationship(
        "SecurityAlert",
        back_populates="incident",
    )
    notes: Mapped[List["InvestigationNote"]] = relationship(
        "InvestigationNote",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="desc(InvestigationNote.created_at)",
    )

    __table_args__ = (
        Index("idx_incidents_status_sev", "status", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Incident {self.incident_number}: {self.title} status={self.status}>"


class InvestigationNote(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    """Immutable forensic journal entry logged by analysts during an incident investigation."""

    __tablename__ = "investigation_notes"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent incident case",
    )
    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Analyst who authored this note",
    )
    note_type: Mapped[NoteType] = mapped_column(
        Enum(NoteType, name="note_type_enum", native_enum=False),
        default=NoteType.GENERAL,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Analyst observation, commands run, IOC hashes, or containment steps taken",
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="notes",
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="investigation_notes",
    )

    def __repr__(self) -> str:
        return f"<InvestigationNote incident={self.incident_id} author={self.author_id}>"
