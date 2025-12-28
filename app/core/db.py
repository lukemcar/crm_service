"""Database layer for the DYNO CRM service.

This module defines the SQLAlchemy engine, session factory and base class
used across the application.  It follows the patterns described in the
Python Developer Guide and mirrors the setup in the Tenant Management
Service for consistency.  The engine is configured via the Config class
and uses connection pooling with `pool_pre_ping` enabled to detect
disconnected connections.
"""

from __future__ import annotations

from typing import Generator, Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import Config

# Create the SQLAlchemy engine using the configured database URL.  The
# pool_pre_ping=True flag ensures the engine checks the connection
# health before each use, preventing the service from using stale
# connections.
engine = create_engine(Config.database_url(), pool_pre_ping=True)

# Session factory for scoped sessions.  autocommit=False and
# autoflush=False follow recommended patterns for explicit transaction
# boundaries in FastAPI services.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for declarative models.  All ORM models in app/domain/models
# must inherit from this Base to register with the SQLAlchemy metadata.
Base = declarative_base()

# Import model modules to ensure they are registered with SQLAlchemy.  These
# imports are enclosed in a try/except so that errors during model
# definition do not prevent the module from loading.  The __all__ list
# remains empty here; the purpose is side‑effects.
try:
    from app.domain.models import (
        contact,
        company,
        deal,
        pipeline,
        pipeline_stage,
        activity,
        list as list_model,  # list is a Python built‑in; alias to avoid clash
        list_membership,
        association,
    )  # noqa: F401
except Exception:
    # Models may not exist yet during bootstrap.  Ignore import errors.
    pass


def get_db() -> Iterator:
    """Provide a transactional database session.

    This function can be used as a FastAPI dependency.  It yields a
    SessionLocal and ensures it is closed after use.  Transactions are
    committed explicitly in the service layer; if an exception occurs,
    the session is rolled back when exiting the context.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """Perform a simple readiness check against the database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        # In practice, log the exception to your logger here
        raise


__all__ = ["engine", "SessionLocal", "Base", "get_db", "check_database_connection"]