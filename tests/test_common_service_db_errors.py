from __future__ import annotations

"""Tests for database error handling helpers in common_service.

These tests verify that database exceptions are translated into meaningful
HTTP errors with appropriate status codes and sanitized detail payloads.
They use dummy error objects and dummy sessions to avoid requiring a real
database connection.
"""

import types

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.services.common_service import (
    _http_exception_from_db_error,
    commit_or_raise,
)


class DummyDiag:
    """Simple container for pg constraint metadata."""

    def __init__(self, constraint_name: str | None = None, message_detail: str | None = None):
        self.constraint_name = constraint_name
        self.message_detail = message_detail


class DummyOrig(Exception):
    """Mimics a DB-API exception with pgcode and diag attributes."""

    def __init__(self, pgcode: str, constraint_name: str | None = None, message_detail: str | None = None):
        super().__init__("dummy orig")
        self.pgcode = pgcode
        self.diag = DummyDiag(constraint_name, message_detail)

    def __str__(self) -> str:
        return "dummy DB error"


def test_http_exception_from_db_error_unique_violation() -> None:
    """Unique constraint violations translate to HTTP 409 and include constraint name."""
    err = types.SimpleNamespace()
    # Set orig with pgcode 23505 (unique violation)
    err.orig = DummyOrig(
        pgcode="23505",
        constraint_name="ux_company_tenant_company_name",
        message_detail="Key (tenant_id, company_name) already exists.",
    )
    exc = _http_exception_from_db_error(err)
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 409
    detail = exc.detail  # type: ignore
    assert detail["constraint"] == "ux_company_tenant_company_name"


def test_http_exception_from_db_error_check_violation_sanitized() -> None:
    """Check constraint violations remove failing row details and include hints if available."""
    err = types.SimpleNamespace()
    err.orig = DummyOrig(
        pgcode="23514",
        constraint_name="ck_company_note_type",
        message_detail="Failing row contains ...",  # Simulate row dump
    )
    exc = _http_exception_from_db_error(err)
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 422
    detail = exc.detail  # type: ignore
    # Ensure the failing row detail has been sanitized
    assert "Failing row contains" not in detail.get("db_detail", "")
    # Should include the constraint name
    assert detail.get("constraint") == "ck_company_note_type"
    # Because this constraint has a hint in CONSTRAINT_HINTS, field and allowed_values should be present
    assert detail.get("field") == "notes[].note_type"
    assert detail.get("allowed_values") == ["note", "call", "meeting", "email", "sms", "other"]


def test_commit_or_raise_rolls_back_on_unique_violation() -> None:
    """commit_or_raise rolls back and raises HTTPException for unique violations."""
    # Prepare a dummy session that will raise an IntegrityError on commit
    class DummySession:
        def __init__(self) -> None:
            self.rollback_called = False
            self.refresh_called = False

        def commit(self) -> None:
            raise IntegrityError(
                statement="INSERT", params={}, orig=DummyOrig(
                    pgcode="23505",
                    constraint_name="ux_company_name",
                    message_detail="Key exists",
                )
            )

        def rollback(self) -> None:
            self.rollback_called = True

        def refresh(self, obj: object) -> None:
            self.refresh_called = True

    db = DummySession()
    obj = types.SimpleNamespace()
    with pytest.raises(HTTPException) as ctx:
        commit_or_raise(db, refresh=obj, action="create_lead")
    assert db.rollback_called is True
    # Refresh should not be called if commit fails
    assert db.refresh_called is False
    assert ctx.value.status_code == 409


def test_commit_or_raise_rolls_back_on_check_violation() -> None:
    """commit_or_raise rolls back and raises HTTPException for check violations."""
    class DummySession:
        def __init__(self) -> None:
            self.rollback_called = False
            self.refresh_called = False

        def commit(self) -> None:
            raise DBAPIError(
                statement="INSERT", params={}, orig=DummyOrig(
                    pgcode="23514",
                    constraint_name="ck_company_note_type",
                    message_detail="Failing row contains ...",
                )
            )

        def rollback(self) -> None:
            self.rollback_called = True

        def refresh(self, obj: object) -> None:
            self.refresh_called = True

    db = DummySession()
    obj = types.SimpleNamespace()
    with pytest.raises(HTTPException) as ctx:
        commit_or_raise(db, refresh=obj, action="add_note")
    assert db.rollback_called is True
    assert db.refresh_called is False
    assert ctx.value.status_code == 422