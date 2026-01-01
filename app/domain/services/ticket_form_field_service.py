"""
Service layer for TicketFormField entities.

This module provides CRUD operations for associations between ticket
forms and custom field definitions, ensuring tenant scoping and
emitting domain events upon successful mutations.  Listing
operations support optional filtering by form or field definition.
Unique constraints are enforced at the database layer; violations
will surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_form_field import TicketFormField
from app.domain.schemas.ticket_form_field import (
    TicketFormFieldUpdate,
    TenantCreateTicketFormField,
    AdminCreateTicketFormField,
)
from app.domain.schemas.events.ticket_form_field_event import (
    TicketFormFieldDelta,
)
from app.messaging.producers.ticket_form_field_producer import (
    TicketFormFieldMessageProducer as TicketFormFieldProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_form_field_service")


def _snapshot(ff: TicketFormField) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketFormField suitable for event payloads."""
    return {
        "id": ff.id,
        "tenant_id": ff.tenant_id,
        "ticket_form_id": ff.ticket_form_id,
        "ticket_field_def_id": ff.ticket_field_def_id,
        "display_order": ff.display_order,
        "created_at": ff.created_at.isoformat() if ff.created_at else None,
        "created_by": ff.created_by,
    }


def _compute_delta(ff: TicketFormField, updates: Dict[str, Any]) -> TicketFormFieldDelta:
    """Compute a delta object for modified base fields on a ticket form field."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(ff, field)
        if current != value:
            changed[field] = value
    return TicketFormFieldDelta(base_fields=changed or None)


def list_ticket_form_fields(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    ticket_form_id: Optional[uuid.UUID] = None,
    ticket_field_def_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketFormField], int]:
    """List ticket form fields with optional filtering by form and field definition.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Optional
    filters on ``ticket_form_id`` and ``ticket_field_def_id`` narrow the list
    further.  Results are ordered by ``display_order`` ascending and can be
    paginated via ``limit`` and ``offset``.  Returns the list of form
    fields and the total count.
    """
    logger.debug(
        "Listing ticket form fields: tenant_id=%s, form_id=%s, field_def_id=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_form_id,
        ticket_field_def_id,
        limit,
        offset,
    )
    query = db.query(TicketFormField)
    if tenant_id:
        query = query.filter(TicketFormField.tenant_id == tenant_id)
    if ticket_form_id:
        query = query.filter(TicketFormField.ticket_form_id == ticket_form_id)
    if ticket_field_def_id:
        query = query.filter(TicketFormField.ticket_field_def_id == ticket_field_def_id)
    total = query.count()
    query = query.order_by(TicketFormField.display_order.asc())
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all(), total


def create_ticket_form_field(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateTicketFormField | AdminCreateTicketFormField,
    created_by: str,
) -> TicketFormField:
    """Create a new ticket form field and publish a created event."""
    logger.debug(
        "Creating ticket form field: tenant_id=%s, form_id=%s, field_def_id=%s, order=%s",
        tenant_id,
        request.ticket_form_id,
        request.ticket_field_def_id,
        request.display_order,
    )
    ff = TicketFormField(
        tenant_id=tenant_id,
        ticket_form_id=request.ticket_form_id,
        ticket_field_def_id=request.ticket_field_def_id,
        display_order=request.display_order,
        created_by=created_by,
    )
    db.add(ff)
    commit_or_raise(db, refresh=ff, action="create ticket form field")
    snapshot = _snapshot(ff)
    TicketFormFieldProducer.send_ticket_form_field_created(
        tenant_id=tenant_id, payload=snapshot
    )
    return ff


def get_ticket_form_field(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    form_field_id: uuid.UUID,
) -> TicketFormField:
    """Retrieve a ticket form field by ID within a tenant context."""
    ff = (
        db.query(TicketFormField)
        .filter(
            TicketFormField.id == form_field_id,
            TicketFormField.tenant_id == tenant_id,
        )
        .first()
    )
    if not ff:
        logger.info(
            "Ticket form field not found: tenant_id=%s, form_field_id=%s",
            tenant_id,
            form_field_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket form field not found"
        )
    return ff


def update_ticket_form_field(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    form_field_id: uuid.UUID,
    request: TicketFormFieldUpdate,
    updated_by: str,
) -> TicketFormField:
    """Update an existing ticket form field and publish an update event."""
    ff = get_ticket_form_field(db, tenant_id=tenant_id, form_field_id=form_field_id)
    updates: Dict[str, Any] = {}
    if request.display_order is not None:
        updates["display_order"] = request.display_order
    delta = _compute_delta(ff, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(ff, field, value)
        # update audit
        # There is no updated_at or updated_by on TicketFormField; created_at and created_by only
        commit_or_raise(db, refresh=ff, action="update ticket form field")
        snapshot = _snapshot(ff)
        TicketFormFieldProducer.send_ticket_form_field_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return ff


def delete_ticket_form_field(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    form_field_id: uuid.UUID,
) -> None:
    """Delete a ticket form field and publish a deletion event."""
    ff = get_ticket_form_field(db, tenant_id=tenant_id, form_field_id=form_field_id)
    db.delete(ff)
    commit_or_raise(db, action="delete ticket form field")
    deleted_dt = datetime.utcnow().isoformat()
    TicketFormFieldProducer.send_ticket_form_field_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_ticket_form_fields",
    "create_ticket_form_field",
    "get_ticket_form_field",
    "update_ticket_form_field",
    "delete_ticket_form_field",
]