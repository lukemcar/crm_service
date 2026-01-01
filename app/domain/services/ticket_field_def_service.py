"""
Service layer for TicketFieldDef entities.

This module provides CRUD operations for custom ticket field
definitions, ensuring tenant scoping and emitting domain events upon
successful mutations.  Listing operations support optional filters
such as field type and active status.  Unique constraints and check
constraints are enforced at the database layer; violations will surface
as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_field_def import TicketFieldDef
from app.domain.schemas.ticket_field_def import (
    TicketFieldDefUpdate,
    TenantCreateTicketFieldDef,
    AdminCreateTicketFieldDef,
)
from app.domain.schemas.events.ticket_field_def_event import TicketFieldDefDelta
from app.messaging.producers.ticket_field_def_producer import (
    TicketFieldDefMessageProducer as TicketFieldDefProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_field_def_service")


def _snapshot(defn: TicketFieldDef) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketFieldDef suitable for event payloads."""
    return {
        "id": defn.id,
        "tenant_id": defn.tenant_id,
        "field_key": defn.field_key,
        "label": defn.label,
        "field_type": defn.field_type,
        "is_required": defn.is_required,
        "is_active": defn.is_active,
        "validation": defn.validation,
        "ui_config": defn.ui_config,
        "created_at": defn.created_at.isoformat() if defn.created_at else None,
        "updated_at": defn.updated_at.isoformat() if defn.updated_at else None,
        "created_by": defn.created_by,
        "updated_by": defn.updated_by,
    }


def _compute_delta(defn: TicketFieldDef, updates: Dict[str, Any]) -> TicketFieldDefDelta:
    """Compute a delta object for modified base fields on a ticket field definition."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(defn, field)
        if current != value:
            changed[field] = value
    return TicketFieldDefDelta(base_fields=changed or None)


def list_ticket_field_defs(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    field_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketFieldDef], int]:
    """List ticket field definitions with optional filtering by type and active status.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``field_type`` filters on the exact field_type value.  ``is_active``
    filters definitions by active status.  Results are ordered by
    creation time descending and can be paginated via ``limit`` and
    ``offset``.  Returns the list of definitions and the total count.
    """
    logger.debug(
        "Listing ticket field defs: tenant_id=%s, field_type=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        field_type,
        is_active,
        limit,
        offset,
    )
    query = db.query(TicketFieldDef)
    if tenant_id:
        query = query.filter(TicketFieldDef.tenant_id == tenant_id)
    if field_type:
        query = query.filter(TicketFieldDef.field_type == field_type)
    if is_active is not None:
        query = query.filter(TicketFieldDef.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketFieldDef.created_at.desc())
    return query.all(), total


def create_ticket_field_def(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateTicketFieldDef | AdminCreateTicketFieldDef,
    created_by: str,
) -> TicketFieldDef:
    """Create a new ticket field definition and publish a created event."""
    logger.debug(
        "Creating ticket field def: tenant_id=%s, field_key=%s, label=%s",
        tenant_id,
        request.field_key,
        request.label,
    )
    # Determine activation status; default to True if not explicitly provided
    is_active = request.is_active if request.is_active is not None else True
    is_required = request.is_required if request.is_required is not None else False
    defn = TicketFieldDef(
        tenant_id=tenant_id,
        field_key=request.field_key,
        label=request.label,
        field_type=request.field_type,
        is_required=is_required,
        is_active=is_active,
        validation=request.validation,
        ui_config=request.ui_config,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(defn)
    commit_or_raise(db, refresh=defn, action="create ticket field definition")
    snapshot = _snapshot(defn)
    TicketFieldDefProducer.send_ticket_field_def_created(
        tenant_id=tenant_id, payload=snapshot
    )
    return defn


def get_ticket_field_def(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
) -> TicketFieldDef:
    """Retrieve a ticket field definition by ID within a tenant context."""
    defn = (
        db.query(TicketFieldDef)
        .filter(
            TicketFieldDef.id == field_def_id,
            TicketFieldDef.tenant_id == tenant_id,
        )
        .first()
    )
    if not defn:
        logger.info(
            "Ticket field def not found: tenant_id=%s, field_def_id=%s", tenant_id, field_def_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket field definition not found"
        )
    return defn


def update_ticket_field_def(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
    request: TicketFieldDefUpdate,
    updated_by: str,
) -> TicketFieldDef:
    """Update an existing ticket field definition and publish an update event."""
    defn = get_ticket_field_def(db, tenant_id=tenant_id, field_def_id=field_def_id)
    updates: Dict[str, Any] = {}
    for field in ["label", "field_type", "is_required", "is_active", "validation", "ui_config"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(defn, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(defn, field, value)
        defn.updated_by = updated_by
        defn.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=defn, action="update ticket field definition")
        snapshot = _snapshot(defn)
        TicketFieldDefProducer.send_ticket_field_def_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return defn


def delete_ticket_field_def(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
) -> None:
    """Delete a ticket field definition and publish a deletion event."""
    defn = get_ticket_field_def(db, tenant_id=tenant_id, field_def_id=field_def_id)
    db.delete(defn)
    commit_or_raise(db, action="delete ticket field definition")
    deleted_dt = datetime.utcnow().isoformat()
    TicketFieldDefProducer.send_ticket_field_def_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_ticket_field_defs",
    "create_ticket_field_def",
    "get_ticket_field_def",
    "update_ticket_field_def",
    "delete_ticket_field_def",
]