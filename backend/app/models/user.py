"""User identity and role definitions for SOC analyst access control."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyUUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import SecurityAlert
    from app.models.audit import AuditEvent
    from app.models.incident import Incident, InvestigationNote
    from app.models.rule import DetectionRule


class UserRole(str, enum.Enum):
    """Role-Based Access Control (RBAC) tiers within the Security Operations Center."""
    ANALYST_TIER_1 = "analyst_tier_1"          # Triage, initial alert review, escalation
    ANALYST_TIER_2 = "analyst_tier_2"          # In-depth analysis, root cause, containment
    INCIDENT_RESPONDER = "incident_responder"  # Active incident management, mitigation
    DETECTION_ENGINEER = "detection_engineer"  # Rule authoring, testing, tuning
    SOC_MANAGER = "soc_manager"                # Metrics, governance, reporting, approvals
    ADMIN = "admin"                            # System administration, user provisioning


class UserStatus(str, enum.Enum):
    """Account operational state."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"


class User(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    """User accounts authorized to access the SOC Sentinel platform."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Primary unique email address for analyst authentication",
    )
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique username/handle for SOC audit attribution",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Argon2/Bcrypt hashed password",
    )
    full_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Full name of analyst or operator",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.ANALYST_TIER_1,
        nullable=False,
        index=True,
        doc="RBAC role assigned to the user",
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status_enum", native_enum=False),
        default=UserStatus.ACTIVE,
        nullable=False,
        doc="Account active or locked state",
    )
    is_mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether multi-factor authentication is configured",
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Counter for brute-force protection lockout",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent successful session authentication",
    )

    # Relationships
    created_rules: Mapped[List["DetectionRule"]] = relationship(
        "DetectionRule",
        back_populates="created_by",
        cascade="all, delete-orphan",
    )
    assigned_alerts: Mapped[List["SecurityAlert"]] = relationship(
        "SecurityAlert",
        back_populates="assigned_to",
    )
    lead_incidents: Mapped[List["Incident"]] = relationship(
        "Incident",
        back_populates="lead_analyst",
    )
    investigation_notes: Mapped[List["InvestigationNote"]] = relationship(
        "InvestigationNote",
        back_populates="author",
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="actor",
    )

    def __repr__(self) -> str:
        return f"<User {self.username} (role={self.role})>"
