"""Base model configuration and common mixins for SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Returns current timestamp with timezone awareness in UTC."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all Sentinel ORM models."""
    pass


class PrimaryKeyUUIDMixin:
    """Provides a standardized UUIDv4 primary key compatible with PostgreSQL & SQLite."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier (UUIDv4) for this record",
    )


class TimestampMixin:
    """Provides timezone-aware creation and modification audit timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="UTC timestamp when record was initially created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        doc="UTC timestamp when record was last updated",
    )
