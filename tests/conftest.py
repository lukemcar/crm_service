"""Shared test fixtures for the DYNO CRM application.

This file defines fixtures for creating a FastAPI TestClient using an
in-memory SQLite database.  Each test session starts with a clean
database schema derived from the ORM models.  The default
database dependency is overridden to use this test database.

We deliberately avoid hitting external services (e.g. Postgres,
RabbitMQ) during unit tests.  Integration tests can be added
separately to exercise the full Docker stack.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db
from main_api import create_app

# Use a file-based SQLite database for persistence across requests in a test run
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine and session factory
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def create_test_database() -> None:
    """Create all tables in the test database before tests run."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    """Dependency override for SQLAlchemy session in tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """Return a FastAPI TestClient with overridden dependencies."""
    app = create_app()
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client