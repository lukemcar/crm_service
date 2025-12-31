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


logger = logging.getLogger("common_service")

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
        # Example: ck_company_note_type
        return HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "message": "A field value failed validation.",
                "constraint": constraint_name,
                "db_detail": detail,
            },
        )

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
]