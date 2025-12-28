"""Configuration utilities for the CRM service.

This module centralises configuration retrieval so that environment variables
are read in one place.  It mirrors the patterns used in other Dyno services.
"""

from __future__ import annotations

import os


class Config:
    """Application configuration loaded from environment variables."""

    @staticmethod
    def database_url() -> str:
        """Return the database URL for SQLAlchemy.

        The default value targets a local PostgreSQL instance.  In production,
        this should be provided via the DATABASE_URL environment variable.
        """
        return os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://crm_user:crm_password@localhost:5432/crm_db",
        )


__all__ = ["Config"]