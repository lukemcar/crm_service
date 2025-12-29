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

    @staticmethod
    def liquibase_enabled() -> bool:
        value = os.getenv("LIQUIBASE_ENABLED", "true").lower()
        return value in {"true", "1", "yes", "y"}

    @staticmethod
    def liquibase_property_file() -> str:
        return os.getenv(
            "LIQUIBASE_PROPERTY_FILE",
            "migrations/liquibase/docker-liquibase.properties",
        )

    @staticmethod
    def jwt_secret() -> str:
        return os.getenv("JWT_SECRET", "2zacRJ76Oj0o5RRyg7nAHtXy09bl6FzS")

    @staticmethod
    def auth0_domain() -> str:
        return os.getenv(
            "AUTH0_DOMAIN", "dev-5f2qcnpxxmrvpvjy.us.auth0.com"
        )

    @staticmethod
    def jwt_algorithm() -> str:
        return os.getenv("JWT_ALGORITHM", "HS256")    
    
    
    @staticmethod
    def celery_broker_url() -> str:
        return os.getenv(
            "CELERY_BROKER_URL",
            "amqp://tenant_service:tenant_service@localhost:5672/tenant_service",
        )

    @staticmethod
    def celery_result_backend() -> str:
        return os.getenv("CELERY_RESULT_BACKEND", "rpc://")


__all__ = ["Config"]