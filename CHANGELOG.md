## [2025-12-31] – DB error handling and rollback standardization

### Added
- Introduced `commit_or_raise` helper in `app/domain/services/common_service.py` to centralize transaction commits.
  The helper commits the SQLAlchemy session, optionally refreshes an ORM instance, and handles all database
  exceptions by rolling back and translating them into meaningful `HTTPException` instances.
- Added a `CONSTRAINT_HINTS` dictionary and improved `_http_exception_from_db_error` to sanitize check
  constraint error messages and include field/allowed value hints for known constraints.
- Created `error_handling_implementation.md` documenting the rationale behind the new helper, the
  sanitization approach, and the steps taken to apply the pattern across services.
- Added tests in `tests/test_common_service_db_errors.py` covering translation of unique and check
  constraint violations and verifying that `commit_or_raise` rolls back sessions appropriately.

### Changed
- Replaced all direct calls to `db.commit()` in `company_service.py`, `contact_service.py`, and
  `lead_service.py` with calls to `commit_or_raise`, ensuring consistent rollback and error translation.
- Updated service functions to supply descriptive `action` names to `commit_or_raise` and passed
  ORM instances to refresh when previously used.
- Sanitized check constraint violations to remove row data from error responses and added constraint
  hints where available.

### Tests
- Added `tests/test_common_service_db_errors.py` verifying the new helper and error translation.
- Updated service tests to accommodate the new error handling (if necessary) and ensure that unique
  and check constraint violations return HTTP 409 and HTTP 422, respectively.

## [2025-12-30] – Postgres-in-Docker Test Harness

### Added
- Introduced a comprehensive test infrastructure that runs database tests
  against a temporary Postgres instance started via Docker Compose.  A new
  `docker-compose.test.yml` defines the test container and mounts the
  existing `init-database.sql` to provision the database and users.
- Added `test-liquibase.properties` to point Liquibase at the test
  database.  Migrations are applied once per test session only when
  tests are marked with `@pytest.mark.liquibase`.
- Added a dedicated `pytest.ini` configuring custom markers (`postgres`,
  `liquibase`, `integration`) and enabling terse output.
- Rewrote `tests/conftest.py` to start/stop the Postgres container,
  apply migrations, create a SQLAlchemy engine, provide transactional
  sessions, and supply a FastAPI `TestClient` that overrides the
  database dependency.  Pure unit tests continue to run without
  starting Docker.
- Added a new test `tests/test_pg_jsonb.py` verifying that JSONB
  columns are usable under Postgres.

### Changed
- Updated `tests/test_contact.py` to use the tenant‑scoped API
  (`/tenants/{tenant_id}/contacts`) and the appropriate nested payload
  structure for phones and emails.  Contact tests now send the user
  identity via the `X-User` header and apply updates via JSON Patch.
- Removed the old SQLite-based test setup; database tests now use
  Postgres exclusively and run within transactions that roll back
  after each test.

### Tests
- All contact API tests are marked with `@pytest.mark.postgres` and
  `@pytest.mark.liquibase` to trigger the Docker container and
  migrations.  A new PG-specific test ensures JSONB columns work
  correctly.

### Notes
- To run the full test suite locally, ensure Docker is installed and
  available.  Then execute `python -m pytest`.  To run only unit
  tests without starting Docker, use `pytest -m "not postgres"`.

## [2025-12-28] – Fix Pydantic Config & Telemetry Initialization

### Added
- New test `tests/test_telemetry.py` ensuring tracing initialization fails gracefully when the OTLP exporter endpoint is not set.

### Changed
- Updated all Pydantic read schemas (`ContactRead`, `CompanyRead`, `PipelineRead`, `PipelineStageRead`, `DealRead`, `ActivityRead`, `ListRead`, `ListMembershipRead`, `AssociationRead`) to use `ConfigDict(from_attributes=True)` instead of the deprecated class‐based `Config.orm_mode`.
- Modified `app/core/telemetry.py` to disable OTLP exporter creation when `OTEL_EXPORTER_OTLP_ENDPOINT` is not configured, preventing connection errors during tests and local development.

### Tests
- Existing tests remain unchanged and continue to pass.
- Added test coverage for graceful telemetry initialization via `tests/test_telemetry.py`.

### Notes
- These changes remove Pydantic v2 deprecation warnings and prevent `ConnectionRefusedError` and logging errors that occurred when the OTLP exporter attempted to connect to `localhost:4318` without a running collector.