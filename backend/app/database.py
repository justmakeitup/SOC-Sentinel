"""Database engine, session management, and lifecycle dependencies.

Provides declarative session handling for FastAPI dependency injection
and database connectivity verification for system health monitoring.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger("sentinel.database")

# Build engine arguments depending on dialect (PostgreSQL vs SQLite for unit testing)
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
pool_kwargs = {} if is_sqlite else {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,  # Proactively test connection freshness
}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated SQLAlchemy database session.

    Guarantees session teardown and rollback on unhandled exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> dict:
    """Verifies database connectivity and returns latency/status details.

    Used by health endpoints to monitor subsystem availability without throwing
    unhandled 500 errors to callers during degraded states.
    """
    import time
    start = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "connected", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return {"status": "disconnected", "error": str(exc)}
