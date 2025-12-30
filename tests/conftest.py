"""Shared test fixtures for the DYNO CRM application.

This test configuration uses a temporary Postgres instance started via
Docker Compose.  The database and required users are provisioned by the
init script in ``docker/postgres/init-database.sql``.  Migrations are
applied via Liquibase only when tests are marked with
``@pytest.mark.liquibase``.  Each test that touches the database runs
within its own transaction, which is rolled back after the test
finishes to ensure isolation.

Pure unit tests that do not need a database or migrations should not
depend on the fixtures defined here.  Such tests will run without
starting the Docker container.
"""

from __future__ import annotations

import os
import time
import subprocess
from pathlib import Path
from typing import Iterator

import psycopg2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.db import get_db
from app.util.liquibase import apply_changelog
from main_api import create_app


# ---------------------------------------------------------------------------
# Database configuration
#
# The values here must align with the docker-compose.test.yml file and the
# init script.  These defaults can be overridden via environment variables.
DB_HOST: str = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("TEST_DB_PORT", "25432"))
DB_NAME: str = os.getenv("TEST_DB_NAME", "crm_service")
DB_USER: str = os.getenv("TEST_DB_USER", "crm_service_app")
DB_PASSWORD: str = os.getenv(
    "TEST_DB_PASSWORD", "2cHfTngNdjFIX78JUz2Z91iDpQKGJPWo"
)

# Path to the test Liquibase properties file.  Tests can override this via
# the TEST_LIQUIBASE_PROPERTY_FILE environment variable.
TEST_LIQUIBASE_PROPERTY_FILE: str = os.getenv(
    "TEST_LIQUIBASE_PROPERTY_FILE", "test-liquibase.properties"
)

# Build the SQLAlchemy database URL for the test engine.  psycopg2 is
# required for SQLAlchemy to communicate with Postgres.
TEST_DATABASE_URL: str = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Location of the docker-compose file used to start the test Postgres
# instance.  The project root is the parent of this tests directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[1]
COMPOSE_FILE: Path = REPO_ROOT / "docker-compose.test.yml"
LIQUIBASE_DEFAULTS_FILE: Path = REPO_ROOT / TEST_LIQUIBASE_PROPERTY_FILE


def _wait_for_postgres(
    host: str, port: int, user: str, password: str, db: str, timeout: int = 60
) -> None:
    """Poll until a connection to Postgres can be established or timeout."""
    start = time.time()
    while True:
        try:
            conn = psycopg2.connect(
                host=host, port=port, user=user, password=password, dbname=db
            )
            conn.close()
            return
        except Exception:
            if time.time() - start > timeout:
                raise RuntimeError("Timed out waiting for Postgres to be ready")
            time.sleep(1)


def _run_liquibase_update() -> None:
    """Invoke Liquibase to apply the database changelog."""
    apply_changelog(property_file=str(LIQUIBASE_DEFAULTS_FILE))


@pytest.fixture(scope="session")
def docker_compose(request: pytest.FixtureRequest) -> Iterator[None]:
    """Start and stop the Postgres Docker container for the test session.

    This fixture runs ``docker compose up --build -d`` before any tests that
    depend on a database are executed and tears down the container at the end
    of the session.  If no tests require the database (i.e., no fixtures
    depend on this fixture), then Docker is not started.
    """
    # Only start Docker if any collected test is marked as needing Postgres or
    # Liquibase.  This check prevents spinning up a container for pure unit
    # tests that do not touch the database.
    has_db_tests = any(
        item.get_closest_marker("postgres") is not None
        or item.get_closest_marker("liquibase") is not None
        for item in request.session.items
    )
    if not has_db_tests:
        yield
        return

    # Run docker compose up to start the Postgres container for tests.
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "--build", "-d"],
        check=True,
    )
    try:
        # Wait for the database to be ready before yielding control to tests.
        _wait_for_postgres(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
        yield
    finally:
        # Tear down and remove volumes to ensure a clean slate for the next
        # session.
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v"],
            check=True,
        )


@pytest.fixture(scope="session")
def liquibase_migrations(
    request: pytest.FixtureRequest, docker_compose: None
) -> Iterator[None]:
    """Apply Liquibase migrations once per session when required.

    If any collected test has the ``liquibase`` marker, this fixture will
    execute the Liquibase update exactly once.  Otherwise, it does nothing.
    """
    has_liquibase_tests = any(
        item.get_closest_marker("liquibase") is not None for item in request.session.items
    )
    if not has_liquibase_tests:
        yield
        return
    _run_liquibase_update()
    yield


@pytest.fixture(scope="session")
def engine(docker_compose: None, liquibase_migrations: None) -> Iterator[create_engine]:
    """Create a SQLAlchemy engine connected to the test database.

    The engine is created once per test session and disposed at teardown.
    """
    engine = create_engine(TEST_DATABASE_URL, future=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(engine: create_engine) -> Iterator[Session]:
    """Provide a database session scoped to a single test with rollback.

    Each test opens a new transaction on the same connection.  At the end of
    the test, the transaction is rolled back and the connection is closed,
    leaving the database in its original state.  This pattern avoids the
    overhead of recreating the schema between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        bind=connection, autoflush=False, autocommit=False, future=True
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_client(db_session: Session) -> Iterator[TestClient]:
    """Return a FastAPI TestClient using the Postgres test database.

    This fixture overrides the ``get_db`` dependency to return the
    transactional session created by ``db_session``.  It also ensures that
    Liquibase is not executed on application startup by setting
    ``LIQUIBASE_ENABLED`` to ``false``.
    """
    # Disable automatic Liquibase migrations on app startup.  Migrations are
    # applied explicitly via the ``liquibase_migrations`` fixture when
    # required.  Environment variables override the Config settings used by
    # ``main_api.create_app``.
    os.environ.setdefault("LIQUIBASE_ENABLED", "false")
    app = create_app()

    # Override the get_db dependency to use our transactional session.
    def override_get_db() -> Iterator[Session]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    # Remove the override after the test to avoid leaking state to other tests.
    app.dependency_overrides.pop(get_db, None)