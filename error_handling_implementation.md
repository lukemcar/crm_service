# Error Handling & Rollback Standardization Implementation Plan

This document captures the design decisions and implementation steps taken to standardize database error handling and transaction rollbacks across the CRM service.  The changes ensure that all mutations use a centralized pattern that properly rolls back failed transactions and translates database errors into meaningful HTTP responses without leaking sensitive information.

## Overview

Several service modules in the project (`company_service`, `contact_service`, `lead_service`) interact directly with SQLAlchemy sessions.  Prior to this work, many functions called `db.commit()` directly, allowing uncaught database exceptions to bubble up as unhandled 500 errors.  Moreover, check constraint violations included full row dumps in the error detail, which could leak personally identifiable data.  To address these issues we introduced:

* A new helper, `commit_or_raise`, in `app/domain/services/common_service.py`.  This function wraps `db.commit()` and optional `db.refresh()` calls, catches database exceptions (`IntegrityError`, `DBAPIError`), performs a rollback, and re‑raises a translated `HTTPException` via `_http_exception_from_db_error`.  Unexpected exceptions are rolled back and surfaced as generic 500 responses.

* Enhanced sanitization in `_http_exception_from_db_error`.  For check constraint violations (SQLSTATE `23514`), the helper now removes the "Failing row contains" payload and optionally injects hint metadata (`field`, `allowed_values`) from the new `CONSTRAINT_HINTS` mapping.  This prevents leaking full row contents while giving API consumers a clear hint about what field failed.

* Constraint hints dictionary (`CONSTRAINT_HINTS`) allowing the system to map database constraint names to user‑friendly metadata.  Currently it contains an entry for `ck_company_note_type` with the allowed values for the `notes[].note_type` field.

* Updated services (`company_service.py`, `contact_service.py`, `lead_service.py`) to use `commit_or_raise` at every commit site.  Each call supplies an `action` string to help with debugging.  Where appropriate, a `refresh` argument ensures the ORM instance is refreshed after commit.  Custom try/except blocks around JSON patch operations continue to roll back when validation fails.

* Tests (added separately) to cover the translation of constraint violations and to verify that service functions return appropriate HTTP status codes for unique and check constraint violations.

## Steps Taken

1. **Introduced `commit_or_raise` helper in `common_service.py`**
   - Imports `DBAPIError`, `IntegrityError` from SQLAlchemy.
   - Accepts a SQLAlchemy session, optional `refresh` object, and an `action` description.
   - Invokes `db.commit()`; if `refresh` is provided, invokes `db.refresh(refresh)`.
   - On `IntegrityError` or `DBAPIError`, rolls back the session and raises a translated `HTTPException` using `_http_exception_from_db_error`.
   - On any other exception, rolls back and raises a generic 500 error with a message that includes the action name.
   - Exports `commit_or_raise` via `__all__` for external import.

2. **Enhanced `_http_exception_from_db_error`**
   - For check constraint violations (SQLSTATE `23514`), sanitizes the Postgres error detail to avoid exposing row contents.
   - Looks up `CONSTRAINT_HINTS` for known constraints and injects `field` and `allowed_values` into the error detail when available.
   - Keeps existing handling for unique (`23505`), foreign key (`23503`), not‑null (`23502`) violations, and generic database errors.

3. **Added `CONSTRAINT_HINTS` mapping**
   - A dictionary mapping constraint names to human‑readable hints.
   - Example entry for `ck_company_note_type` specifying the field `notes[].note_type` and its allowed values.

4. **Modified Service Modules**
   - Imported `commit_or_raise` into `company_service.py`, `contact_service.py`, and `lead_service.py`.
   - Replaced every call to `db.commit()` (and corresponding `db.refresh()`) with calls to `commit_or_raise`, passing `refresh` where a refresh was previously performed.
   - Supplied descriptive `action` names such as `"create_company"`, `"update_contact_phone"`, or `"delete_lead"` to aid debugging.
   - Left business logic, event emission, and DTO mapping untouched; changes only affect transaction handling.
   - Retained existing validation and HTTP exception flows in JSON patch functions, with manual rollbacks for non‑database errors to preserve atomic behaviour.

5. **Copied Updated Files into Project Structure**
   - After patching root‑level service files, they were copied into the extracted repository under `app/domain/services/` to ensure they are packaged in the final zip.

6. **Updated `CHANGELOG.md` (top entry)**
   - Added a new entry describing the addition of `commit_or_raise` and the standardized error handling across services.
   - Noted the sanitization of check constraint messages and the introduction of constraint hints.

7. **Added Tests**
   - Added a new test module to verify that `_http_exception_from_db_error` translates unique and check constraint violations into `HTTPException` objects with the correct status codes (`409`, `422`) and sanitized messages.
   - Added service tests that simulate unique and check constraint violations using mocked SQLAlchemy sessions and ensure that service functions return appropriate errors via FastAPI.

## Future Considerations

* **Extensibility of `CONSTRAINT_HINTS`**: As new check constraints are added to the database schema, entries should be added to `CONSTRAINT_HINTS` to provide clean feedback to API consumers.  Without a hint, only a generic validation message is returned.

* **Outbox/Retry Patterns**: Currently, if event publishing fails after a successful commit, the API still returns a 500 error.  For a more resilient system, an outbox table and background retry could decouple event delivery from the HTTP response, ensuring that the API returns success whenever the database mutation succeeds.

* **Thread‑safety and Sessions**: The helper assumes the provided session is scoped per request.  It rolls back on failure, but callers must still handle disposal and creation of new sessions as appropriate for their frameworks.

This implementation plan ensures consistent, sanitized error handling across the CRM service while maintaining existing behaviour and event semantics.  It centralizes transaction management in a single helper, reduces duplication, and provides clear feedback to API clients.