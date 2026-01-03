"""
Service layer for tenant user shadow projections.

This module provides read‑only access to the ``tenant_user_shadow``
projections.  It exposes helper functions to list users for a
tenant and retrieve a single user by composite key.  No create,
update or delete operations are provided because the CRM does not
own these records; they are maintained by the tenant management
service and mirrored in CRM via asynchronous events.

The service follows patterns established in other domain services:
database access via SQLAlchemy Session, explicit tenant scoping on
queries and robust logging.  Errors such as missing rows are
translated into HTTP exceptions for use in FastAPI endpoints.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.tenant_user_shadow import TenantUserShadow
from app.domain.schemas.tenant_user_shadow import CreateTenantUserShadow

from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("tenant_user_shadow_service")


def list_tenant_users(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TenantUserShadow], int]:
    """List projected users for a tenant with optional filtering.

    Parameters
    ----------
    db : Session
        The SQLAlchemy session used for the query.
    tenant_id : uuid.UUID
        Identifier of the tenant to scope the query.
    display_name : Optional[str], optional
        Case‑insensitive substring match on the user's display name.
    email : Optional[str], optional
        Case‑insensitive substring match on the user's email address.
    limit : Optional[int], optional
        Maximum number of results to return.  If None, return all.
    offset : Optional[int], optional
        Number of records to skip before returning results.

    Returns
    -------
    Tuple[List[TenantUserShadow], int]
        A tuple of (results, total_count).  ``results`` is a list of
        TenantUserShadow instances; ``total_count`` is the total number of
        records matching the criteria regardless of pagination.
    """
    logger.debug(
        "Listing tenant user shadows: tenant_id=%s, display_name=%s, email=%s, limit=%s, offset=%s",
        tenant_id,
        display_name,
        email,
        limit,
        offset,
    )
    query = db.query(TenantUserShadow).filter(TenantUserShadow.tenant_id == tenant_id)
    if display_name:
        ilike_pattern = f"%{display_name.lower()}%"
        query = query.filter(
            # case-insensitive match on display_name
            TenantUserShadow.display_name.ilike(ilike_pattern)
        )
    if email:
        ilike_pattern = f"%{email.lower()}%"
        query = query.filter(TenantUserShadow.email.ilike(ilike_pattern))

    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    # Order results by created_at descending to match other list endpoints
    query = query.order_by(TenantUserShadow.created_at.desc())

    results = query.all()
    return results, total


def get_tenant_user(
    db: Session, *, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> TenantUserShadow:
    """Retrieve a single tenant user projection by composite key.

    Raises HTTP 404 if no matching record is found.
    """
    logger.debug(
        "Fetching tenant user shadow: tenant_id=%s, user_id=%s", tenant_id, user_id
    )
    instance = (
        db.query(TenantUserShadow)
        .filter(
            TenantUserShadow.tenant_id == tenant_id,
            TenantUserShadow.user_id == user_id,
        )
        .first()
    )
    if instance is None:
        logger.info(
            "Tenant user shadow not found: tenant_id=%s, user_id=%s", tenant_id, user_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant user projection not found",
        )
    return instance


def create_tenant_user_shadow(
    db: Session, *, user_in: CreateTenantUserShadow
) -> TenantUserShadow:
    """Create a new tenant user shadow projection.

    This function is intended for use by event handlers that
    synchronize tenant user data from the tenant management service.
    """
    logger.debug(
        "Creating tenant user shadow: tenant_id=%s, user_id=%s",
        user_in.tenant_id,
        user_in.user_id,
    )
    instance = TenantUserShadow(
        tenant_id=user_in.tenant_id,
        user_id=user_in.user_id,
        display_name=user_in.display_name,
        email=user_in.email,
        created_at=user_in.created_at,
        updated_at=user_in.updated_at,
    )
    db.add(instance)
    commit_or_raise(db, refresh=instance, action="Created tenant user shadow")
    logger.info(
        "Created tenant user shadow: tenant_id=%s, user_id=%s",
        instance.tenant_id,
        instance.user_id,
    )
    return instance 


__all__ = [
    "list_tenant_users",
    "get_tenant_user",
]
