"""
Service layer for SupportView entities.

This module provides CRUD operations for support views, ensuring tenant
scoping and emitting domain events upon successful mutations.  Listing
operations support optional filtering by activation status.  Unique
constraints are enforced at the database layer; violations will
surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.support_view import SupportView
from app.domain.schemas.support_view import (
    SupportViewUpdate,
    TenantCreateSupportView,
    AdminCreateSupportView,
)
from app.domain.schemas.events.support_view_event import SupportViewDelta
from app.messaging.producers.support_view_producer import (
    SupportViewMessageProducer as SupportViewProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("support_view_service")


def _snapshot(view: SupportView) -> Dict[str, Any]:
    """Return a dictionary representation of a SupportView suitable for event payloads."""
    return {
        "id": view.id,
        "tenant_id": view.tenant_id,
        "name": view.name,
        "description": view.description,
        "is_active": view.is_active,
        "filter_definition": view.filter_definition,
        "sort_definition": view.sort_definition,
        "created_at": view.created_at.isoformat() if view.created_at else None,
        "updated_at": view.updated_at.isoformat() if view.updated_at else None,
        "created_by": view.created_by,
        "updated_by": view.updated_by,
    }


def _compute_delta(view: SupportView, updates: Dict[str, Any]) -> SupportViewDelta:
    """Compute a delta object for modified base fields on a support view."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(view, field)
        if current != value:
            changed[field] = value
    return SupportViewDelta(base_fields=changed or None)


def list_support_views(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[SupportView], int]:
    """List support views with optional filtering by active status and tenant.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``is_active`` filters views by activation status.  Results are
    ordered by creation time descending and can be paginated via
    ``limit`` and ``offset``.  Returns the list of views and the total
    count.
    """
    logger.debug(
        "Listing support views: tenant_id=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        is_active,
        limit,
        offset,
    )
    query = db.query(SupportView)
    if tenant_id:
        query = query.filter(SupportView.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(SupportView.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(SupportView.created_at.desc())
    return query.all(), total


def create_support_view(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateSupportView | AdminCreateSupportView,
    created_by: str,
) -> SupportView:
    """Create a new support view and publish a created event."""
    logger.debug(
        "Creating support view: tenant_id=%s, name=%s",
        tenant_id,
        request.name,
    )
    is_active = request.is_active if request.is_active is not None else True
    view = SupportView(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        is_active=is_active,
        filter_definition=request.filter_definition,
        sort_definition=request.sort_definition,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(view)
    commit_or_raise(db, refresh=view, action="create support view")
    snapshot = _snapshot(view)
    SupportViewProducer.send_support_view_created(tenant_id=tenant_id, payload=snapshot)
    return view


def get_support_view(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
) -> SupportView:
    """Retrieve a support view by ID within a tenant context."""
    view = (
        db.query(SupportView)
        .filter(
            SupportView.id == view_id,
            SupportView.tenant_id == tenant_id,
        )
        .first()
    )
    if not view:
        logger.info("Support view not found: tenant_id=%s, view_id=%s", tenant_id, view_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support view not found")
    return view


def update_support_view(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
    request: SupportViewUpdate,
    updated_by: str,
) -> SupportView:
    """Update an existing support view and publish an update event."""
    view = get_support_view(db, tenant_id=tenant_id, view_id=view_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "description", "is_active", "filter_definition", "sort_definition"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(view, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(view, field, value)
        view.updated_by = updated_by
        view.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=view, action="update support view")
        snapshot = _snapshot(view)
        SupportViewProducer.send_support_view_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return view


def delete_support_view(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
) -> None:
    """Delete a support view and publish a deletion event."""
    view = get_support_view(db, tenant_id=tenant_id, view_id=view_id)
    db.delete(view)
    commit_or_raise(db, action="delete support view")
    deleted_dt = datetime.utcnow().isoformat()
    SupportViewProducer.send_support_view_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_support_views",
    "create_support_view",
    "get_support_view",
    "update_support_view",
    "delete_support_view",
]