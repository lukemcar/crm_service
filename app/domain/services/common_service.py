"""
Service layer for common error handling and utilities.

This module provides helper functions for handling database errors
and translating them into appropriate HTTP exceptions for FastAPI
endpoints.  It centralizes common patterns for error extraction and
response generation.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError, IntegrityError


logger = logging.getLogger("common_service")

# Define hints for known DB check constraints.  These hints map constraint names
# to user‑friendly fields and allowed values.  When a check violation occurs
# these hints will be included in the response to provide actionable
# feedback to API consumers without leaking PII or full row contents.  Only
# include constraints that are defined in the schema; add entries here as
# necessary.
CONSTRAINT_HINTS: dict[str, dict[str, object]] = {
    "ck_company_note_type": {
        "field": "notes[].note_type",
        "allowed_values": ["note", "call", "meeting", "email", "sms", "other"],
    },
    # Add additional constraint hints here if new check constraints are introduced
}


def commit_or_raise(db, *, refresh: object | None = None, action: str | None = None) -> None:
    """
    Commit the current transaction on the provided SQLAlchemy Session and
    optionally refresh the given instance.  If the commit fails due to a
    database integrity or API error, rollback the transaction and raise
    a translated HTTPException.  Any unexpected exception will also
    trigger a rollback and result in a generic 500 error.

    Parameters
    ----------
    db : Session
        The SQLAlchemy session to commit.
    refresh : object, optional
        A mapped instance to refresh after successful commit.
    action : str, optional
        A human‑readable description of the operation being performed.  This
        is used only for error messages when an unexpected exception
        occurs.

    Raises
    ------
    HTTPException
        On any database error translated via `_http_exception_from_db_error` or
        generic unexpected error.
    """
    try:
        db.commit()
        if refresh is not None:
            db.refresh(refresh)
    except IntegrityError as exc:
        # Rollback and translate common integrity errors into HTTP responses
        db.rollback()
        raise _http_exception_from_db_error(exc) from exc
    except DBAPIError as exc:
        # Rollback and translate DBAPI errors
        db.rollback()
        raise _http_exception_from_db_error(exc) from exc
    except Exception as exc:
        # Rollback and raise a generic 500 error for any unexpected exception
        db.rollback()
        # Include action if provided to help identify failing operation
        err_msg = "Unexpected error while performing database operation"
        if action:
            err_msg = f"Unexpected error while {action}"
        raise HTTPException(status_code=500, detail=err_msg) from exc

# ---------------------------------------------------------------------------
# Helper functions for DB error handling
# ---------------------------------------------------------------------------


def _extract_pg_details(err: BaseException) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Best-effort extraction of useful Postgres fields from psycopg2 error objects.
    Returns: (constraint_name, pgcode, detail, message)
    """
    orig = getattr(err, "orig", None) or err
    diag = getattr(orig, "diag", None)

    constraint_name = getattr(diag, "constraint_name", None)
    pgcode = getattr(orig, "pgcode", None)
    detail = getattr(orig, "diag", None) and getattr(orig.diag, "message_detail", None)
    message = str(orig) if orig is not None else str(err)

    return constraint_name, pgcode, detail, message


def _http_exception_from_db_error(err: BaseException) -> HTTPException:
    """
    Translate common DB failures into meaningful HTTP errors.
    - Unique violations => 409 Conflict
    - FK violations => 409 Conflict (or 422 depending on preference)
    - Not-null / check violations => 422 Unprocessable Entity
    - Everything else => 500
    """
    constraint_name, pgcode, detail, message = _extract_pg_details(err)

    # Postgres SQLSTATE codes:
    # 23505 unique_violation
    # 23503 foreign_key_violation
    # 23502 not_null_violation
    # 23514 check_violation
    if pgcode == "23505":
        # Example: ux_company_tenant_company_name
        return HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "message": "A resource with the same unique value already exists.",
                "constraint": constraint_name,
                "db_detail": detail,
            },
        )

    if pgcode == "23503":
        return HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "message": "A related resource was not found or cannot be referenced.",
                "constraint": constraint_name,
                "db_detail": detail,
            },
        )

    if pgcode == "23502":
        return HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "message": "A required field was missing.",
                "constraint": constraint_name,
                "db_detail": detail,
            },
        )

    if pgcode == "23514":
        # Example: check constraint violation.  Sanitize the detail to avoid
        # leaking full row contents.  If the database detail contains
        # "Failing row contains", strip it out.  Additionally include
        # constraint hints when available.
        safe_detail = None
        if detail:
            # Remove full row dump if present
            if isinstance(detail, str) and "Failing row contains" in detail:
                safe_detail = "Check constraint violated."
            else:
                safe_detail = detail
        err_detail = {
            "error": "validation_error",
            "message": "A field value failed validation.",
            "constraint": constraint_name,
            "db_detail": safe_detail,
        }
        hint = CONSTRAINT_HINTS.get(constraint_name)
        if hint:
            # Provide user‑friendly field path and allowed values when known
            field = hint.get("field")
            allowed = hint.get("allowed_values")
            if field:
                err_detail["field"] = field
            if allowed is not None:
                err_detail["allowed_values"] = allowed
        return HTTPException(status_code=422, detail=err_detail)

    # Fallback
    return HTTPException(
        status_code=500,
        detail={
            "error": "database_error",
            "message": "Database operation failed.",
            "constraint": constraint_name,
            "db_detail": detail,
            "db_message": message,
        },
    )
    
__all__ = [
    "_http_exception_from_db_error",
    "commit_or_raise",
]