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
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:///:memory:"):
    from pathlib import Path
    raw_path = db_url.replace("sqlite:///", "")
    p = Path(raw_path)
    if not p.is_absolute():
        backend_dir = Path(__file__).resolve().parent.parent
        resolved = (backend_dir / p).resolve()
        db_url = f"sqlite:///{resolved.as_posix()}"

is_sqlite = db_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
pool_kwargs = {} if is_sqlite else {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,  # Proactively test connection freshness
}

engine = create_engine(
    db_url,
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
