"""SOC compliance and regulatory audit trail logging for administrative and analyst actions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyUUIDMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class AuditEvent(Base, PrimaryKeyUUIDMixin):
    """Immutable audit entry recording SOC operator activities and system governance changes.

    Ensures non-repudiation for incident status alterations, rule modifications,
    and user access reviews as mandated by SOC 2, ISO 27001, and NIST CSF.
    """

    __tablename__ = "audit_events"

    actor_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User who initiated the action; null indicates automated background system event",
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Specific governance verb (e.g., 'RULE_ACTIVATED', 'INCIDENT_ESCALATED', 'ALERT_STATUS_UPDATED')",
    )
    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Target entity type (e.g., 'user', 'detection_rule', 'security_alert', 'incident')",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="Primary identifier of modified resource",
    )
    client_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="Network origin IP address of analyst session",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Browser or API client string",
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="State change differential (before/after parameters) and execution metadata",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Exact UTC timestamp of action execution",
    )

    # Relationships
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_events",
    )

    __table_args__ = (
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_action_time", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditEvent action={self.action} target={self.resource_type}:{self.resource_id} at={self.created_at}>"
