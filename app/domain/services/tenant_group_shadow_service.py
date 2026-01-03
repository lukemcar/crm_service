"""
Service layer for tenant group shadow projections.

Provides read‑only access to the ``tenant_group_shadow`` table.  Functions
include listing groups within a tenant and retrieving a single group by
its identifier.  The CRM does not allow creating, updating or
deleting group projections; they are synchronised from the tenant
service via asynchronous events.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.tenant_group_shadow import TenantGroupShadow
from app.domain.schemas.tenant_group_shadow import CreateTenantGroupShadow

from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("tenant_group_shadow_service")


def list_tenant_groups(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    name: Optional[str] = None,
    key: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TenantGroupShadow], int]:
    """List projected groups for a tenant with optional filtering.

    Parameters mirror those of other list functions.  Filters use
    case‑insensitive substring matching on group_name and exact matching
    on group_key when provided.
    """
    logger.debug(
        "Listing tenant group shadows: tenant_id=%s, name=%s, key=%s, limit=%s, offset=%s",
        tenant_id,
        name,
        key,
        limit,
        offset,
    )
    query = db.query(TenantGroupShadow).filter(TenantGroupShadow.tenant_id == tenant_id)
    if name:
        ilike_pattern = f"%{name.lower()}%"
        query = query.filter(TenantGroupShadow.group_name.ilike(ilike_pattern))
    if key:
        query = query.filter(TenantGroupShadow.group_key == key)

    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TenantGroupShadow.created_at.desc())
    return query.all(), total


def get_tenant_group(
    db: Session, *, tenant_id: uuid.UUID, group_id: uuid.UUID
) -> TenantGroupShadow:
    """Retrieve a single tenant group projection by id.

    Raises HTTP 404 if the group does not exist for the tenant.
    """
    logger.debug(
        "Fetching tenant group shadow: tenant_id=%s, group_id=%s", tenant_id, group_id
    )
    instance = (
        db.query(TenantGroupShadow)
        .filter(
            TenantGroupShadow.tenant_id == tenant_id,
            TenantGroupShadow.id == group_id,
        )
        .first()
    )
    if instance is None:
        logger.info(
            "Tenant group shadow not found: tenant_id=%s, group_id=%s", tenant_id, group_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant group projection not found",
        )
    return instance


    
def create_tenant_group_shadow(
    db: Session,
    *,
    group_in: CreateTenantGroupShadow,
) -> TenantGroupShadow:
    """Create a tenant group shadow projection.

    This function is provided for completeness, but in practice
    tenant group shadows are created and managed by the tenant
    service via asynchronous events.
    """
    logger.debug(
        "Creating tenant group shadow: tenant_id=%s, group_name=%s",
        group_in.tenant_id,
        group_in.group_name,
    )
    instance = TenantGroupShadow(
        tenant_id=group_in.tenant_id,
        group_name=group_in.group_name,
        group_key=group_in.group_key,
        description=group_in.description,
        is_active=group_in.is_active,
    )
    db.add(instance)
    commit_or_raise(db, refresh=instance, action="Created tenant group shadow")
    logger.info(
        "Created tenant group shadow: tenant_id=%s, group_id=%s",
        instance.tenant_id,
        instance.id,
    )
    return instance


__all__ = [
    "list_tenant_groups",
    "get_tenant_group",
]
