"""
Service layer for SupportMacro entities.

This module provides CRUD operations for support macros, ensuring
tenant scoping and emitting domain events upon successful mutations.
Listing operations support optional filtering by activation status.
Unique constraints are enforced at the database layer; violations
surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.support_macro import SupportMacro
from app.domain.schemas.support_macro import (
    SupportMacroUpdate,
    TenantCreateSupportMacro,
    AdminCreateSupportMacro,
)
from app.domain.schemas.events.support_macro_event import SupportMacroDelta
from app.messaging.producers.support_macro_producer import (
    SupportMacroMessageProducer as SupportMacroProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("support_macro_service")


def _snapshot(macro: SupportMacro) -> Dict[str, Any]:
    """Return a dictionary representation of a SupportMacro suitable for event payloads."""
    return {
        "id": macro.id,
        "tenant_id": macro.tenant_id,
        "name": macro.name,
        "description": macro.description,
        "is_active": macro.is_active,
        "actions": macro.actions,
        "created_at": macro.created_at.isoformat() if macro.created_at else None,
        "updated_at": macro.updated_at.isoformat() if macro.updated_at else None,
        "created_by": macro.created_by,
        "updated_by": macro.updated_by,
    }


def _compute_delta(macro: SupportMacro, updates: Dict[str, Any]) -> SupportMacroDelta:
    """Compute a delta object for modified base fields on a support macro."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(macro, field)
        if current != value:
            changed[field] = value
    return SupportMacroDelta(base_fields=changed or None)


def list_support_macros(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[SupportMacro], int]:
    """List support macros with optional filtering by active status and tenant.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``is_active`` filters macros by activation status.  Results are
    ordered by creation time descending and can be paginated via
    ``limit`` and ``offset``.  Returns the list of macros and the
    total count.
    """
    logger.debug(
        "Listing support macros: tenant_id=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        is_active,
        limit,
        offset,
    )
    query = db.query(SupportMacro)
    if tenant_id:
        query = query.filter(SupportMacro.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(SupportMacro.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(SupportMacro.created_at.desc())
    return query.all(), total


def create_support_macro(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateSupportMacro | AdminCreateSupportMacro,
    created_by: str,
) -> SupportMacro:
    """Create a new support macro and publish a created event."""
    logger.debug(
        "Creating support macro: tenant_id=%s, name=%s",
        tenant_id,
        request.name,
    )
    is_active = request.is_active if request.is_active is not None else True
    macro = SupportMacro(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        is_active=is_active,
        actions=request.actions,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(macro)
    commit_or_raise(db, refresh=macro, action="create support macro")
    snapshot = _snapshot(macro)
    SupportMacroProducer.send_support_macro_created(tenant_id=tenant_id, payload=snapshot)
    return macro


def get_support_macro(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    macro_id: uuid.UUID,
) -> SupportMacro:
    """Retrieve a support macro by ID within a tenant context."""
    macro = (
        db.query(SupportMacro)
        .filter(
            SupportMacro.id == macro_id,
            SupportMacro.tenant_id == tenant_id,
        )
        .first()
    )
    if not macro:
        logger.info("Support macro not found: tenant_id=%s, macro_id=%s", tenant_id, macro_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support macro not found")
    return macro


def update_support_macro(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    macro_id: uuid.UUID,
    request: SupportMacroUpdate,
    updated_by: str,
) -> SupportMacro:
    """Update an existing support macro and publish an update event."""
    macro = get_support_macro(db, tenant_id=tenant_id, macro_id=macro_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "description", "is_active", "actions"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(macro, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(macro, field, value)
        macro.updated_by = updated_by
        macro.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=macro, action="update support macro")
        snapshot = _snapshot(macro)
        SupportMacroProducer.send_support_macro_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return macro


def delete_support_macro(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    macro_id: uuid.UUID,
) -> None:
    """Delete a support macro and publish a deletion event."""
    macro = get_support_macro(db, tenant_id=tenant_id, macro_id=macro_id)
    db.delete(macro)
    commit_or_raise(db, action="delete support macro")
    deleted_dt = datetime.utcnow().isoformat()
    SupportMacroProducer.send_support_macro_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_support_macros",
    "create_support_macro",
    "get_support_macro",
    "update_support_macro",
    "delete_support_macro",
]