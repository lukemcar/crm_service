## [2025-12-30] – CRM AI Code Review Hardening

### Added
- New tests for contact CRUD endpoints (`tests/test_contact.py`) exercising create, retrieve, patch and delete operations against tenant-scoped routes.
- New tests for company CRUD endpoints (`tests/test_company.py`) mirroring the contact tests for the company domain.
- New tests for message producers (`tests/test_producers.py`) that patch the `BaseProducer._send` method to assert correct task names, payloads and headers for contact and company events.
- New tests for Celery configuration (`tests/test_celery_config.py`) asserting that the exchange name is `crm` and that task routes for contact and company actions map to the correct queues and routing keys.

### Changed
- Rewrote `app/core/celery_app.py` specifically for the CRM service.  The Celery app now uses the `crm` exchange, defines per-domain queues and dead‑letter queues, and registers task routes for all CRUD actions across CRM domains.  Telemetry initialization remains conditional.
- Updated `app/domain/services/contact_service.py` to remove usage of a `job_title` attribute on the `Contact` ORM model.  The create and patch functions no longer set or clone this transient attribute, avoiding runtime errors.
- Updated `app/domain/services/company_service.py` to correct imports, map Pydantic fields (`name`, `website`) to ORM attributes (`company_name`, `domain`), handle nested collections properly and build deltas using internal field names.  Added convenience properties `name` and `website` to `Company` model via attributes (implemented in a prior commit).
- Fixed numerous import paths in API route modules (`contacts_*_route.py`, `companies_*_route.py`) to reference modules within `app.domain.services`, `app.domain.schemas` and `app.core.db`.  Ensured that tenant and admin routers are included in the FastAPI application via `main_api.create_app`.
- Added and updated tests in `tests/` to use the correct application factory (`main_api.create_app`) and to override the database dependency with an in‑memory SQLite database for deterministic unit tests.

### Notes
- The tests provided in this commit rely on `pytest`, `fastapi[test]` and `SQLAlchemy` to run locally.  They assume that `pytest` is installed in the developer environment.  Each test session initializes a fresh SQLite database and overrides the FastAPI dependency for the DB session.
- The Celery configuration uses environment variables `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.  When running a worker locally, ensure these variables point to a RabbitMQ instance or use the defaults defined in `app/core/config.py`.

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