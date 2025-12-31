import os
import time
import subprocess
from pathlib import Path

import psycopg2
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.util.liquibase import apply_changelog

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Project root (crm_service/)
REPO_ROOT = Path(__file__).resolve().parents[1]

# Optional: load environment variables from .env.test using python-dotenv
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

# If python-dotenv is available and .env.test exists, load it
if load_dotenv is not None:
    env_file = REPO_ROOT / ".env.test"
    if env_file.exists():
        load_dotenv(env_file)


# ---------------------------------------------------------------------------
# Database configuration (test-only)
# ---------------------------------------------------------------------------
# Defaults align with docker-compose.test.yml and docker/postgres/init-database.sql
# These can be overridden via real env vars or .env.test.

DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = int(os.getenv("TEST_DB_PORT", "25432"))

# These match docker/postgres/init-database.sql
DB_NAME = os.getenv("TEST_DB_NAME", "crm_service")
DB_USER = os.getenv("TEST_DB_USER", "crm_service_app")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "2cHfTngNdjFIX78JUz2Z91iDpQKGJPWo")

# Use a test-specific Liquibase properties file in migrations/liquibase/
LIQUIBASE_PROPERTY_FILE = os.getenv(
    "TEST_LIQUIBASE_PROPERTY_FILE",
    "test-liquibase.properties",
)

# SQLAlchemy connection URL for the test database
TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:"
    f"{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# ---------------------------------------------------------------------------
# Paths that depend on REPO_ROOT / LIQUIBASE_PROPERTY_FILE
# ---------------------------------------------------------------------------

# Path to docker-compose.test.yml (project root)
COMPOSE_FILE = REPO_ROOT / "docker-compose.test.yml"

# Path to Liquibase properties file
LIQUIBASE_DEFAULTS_FILE = REPO_ROOT / "migrations" / "liquibase" / LIQUIBASE_PROPERTY_FILE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_postgres(
    host: str,
    port: int,
    user: str,
    password: str,
    db: str,
    timeout: int = 90,
) -> None:
    """
    Polls Postgres until it is ready to accept connections or the timeout expires.
    """
    start = time.time()
    while True:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=db,
            )
            conn.close()
            return
        except Exception:
            if time.time() - start > timeout:
                raise RuntimeError("Timed out waiting for Postgres to be ready")
            time.sleep(1)


def _run_liquibase_update() -> None:
    """
    Runs Liquibase using the same pyliquibase-based helper that production uses,
    but with a test-specific Liquibase properties file.
    """
    apply_changelog(property_file=str(LIQUIBASE_DEFAULTS_FILE))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def docker_compose():
    """
    Session-scoped fixture that starts the Postgres test container
    using docker compose and tears it down at the end of the test session.
    """
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "--build", "-d"],
        check=True,
    )

    try:
        # IMPORTANT:
        # Wait using the postgres superuser against the default postgres DB first.
        # This avoids failing readiness checks if init scripts haven't finished
        # creating crm_service + crm_service_app yet.
        _wait_for_postgres(
            host=DB_HOST,
            port=DB_PORT,
            user=os.getenv("TEST_ADMIN_DB_USER", "postgres"),
            password=os.getenv("TEST_ADMIN_DB_PASSWORD", "postgres"),
            db=os.getenv("TEST_ADMIN_DB_NAME", "postgres"),
        )

        # Then wait for the actual target DB/user to be usable
        _wait_for_postgres(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
        )

        yield
    finally:
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v"],
            check=True,
        )


@pytest.fixture(scope="session")
def liquibase_migrations(request, docker_compose):
    """
    Session-scoped fixture that runs Liquibase migrations once
    if any collected test is marked with @pytest.mark.liquibase.
    """
    has_liquibase_tests = any(
        item.get_closest_marker("liquibase") is not None
        for item in request.session.items
    )

    if not has_liquibase_tests:
        yield
        return

    _run_liquibase_update()
    yield


@pytest.fixture(scope="session")
def engine(docker_compose, liquibase_migrations):
    """
    Session-scoped SQLAlchemy engine backed by the Postgres test database.
    """
    engine = create_engine(TEST_DATABASE_URL, future=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(engine) -> Session:
    """
    Per-test SQLAlchemy Session fixture with rollback isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
