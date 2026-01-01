"""
Service layer for TicketFieldValue entities.

This module provides CRUD operations for custom field values attached
to tickets, ensuring tenant scoping and emitting domain events upon
successful mutations.  Listing operations support optional filtering
by field definition.  Only one of the value fields should be set when
creating or updating a value; this is not enforced here but should be
validated at the API layer or by the caller.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_field_value import TicketFieldValue
from app.domain.schemas.ticket_field_value import (
    TicketFieldValueUpdate,
    TenantCreateTicketFieldValue,
    AdminCreateTicketFieldValue,
)
from app.domain.schemas.events.ticket_field_value_event import (
    TicketFieldValueDelta,
)
from app.messaging.producers.ticket_field_value_producer import (
    TicketFieldValueMessageProducer as TicketFieldValueProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_field_value_service")


def _snapshot(val: TicketFieldValue) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketFieldValue suitable for event payloads."""
    return {
        "id": val.id,
        "tenant_id": val.tenant_id,
        "ticket_id": val.ticket_id,
        "ticket_field_def_id": val.ticket_field_def_id,
        "value_text": val.value_text,
        "value_number": float(val.value_number) if val.value_number is not None else None,
        "value_bool": val.value_bool,
        "value_date": val.value_date.isoformat() if val.value_date else None,
        "value_ts": val.value_ts.isoformat() if val.value_ts else None,
        "value_json": val.value_json,
        "created_at": val.created_at.isoformat() if val.created_at else None,
        "updated_at": val.updated_at.isoformat() if val.updated_at else None,
        "created_by": val.created_by,
        "updated_by": val.updated_by,
    }


def _compute_delta(val: TicketFieldValue, updates: Dict[str, Any]) -> TicketFieldValueDelta:
    """Compute a delta object for modified base fields on a ticket field value."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        # Skip None values
        if value is None:
            continue
        current = getattr(val, field)
        # For numeric values, convert decimals to floats for comparison
        if current != value:
            changed[field] = value
    return TicketFieldValueDelta(base_fields=changed or None)


def list_ticket_field_values(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    ticket_field_def_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketFieldValue], int]:
    """List ticket field values for a specific ticket within a tenant.

    Optionally filter by a specific field definition.  Results are ordered
    by creation time ascending and can be paginated.  Returns the list
    of values and the total count.
    """
    logger.debug(
        "Listing ticket field values: tenant_id=%s, ticket_id=%s, field_def_id=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        ticket_field_def_id,
        limit,
        offset,
    )
    query = db.query(TicketFieldValue).filter(
        TicketFieldValue.tenant_id == tenant_id,
        TicketFieldValue.ticket_id == ticket_id,
    )
    if ticket_field_def_id:
        query = query.filter(
            TicketFieldValue.ticket_field_def_id == ticket_field_def_id
        )
    total = query.count()
    query = query.order_by(TicketFieldValue.created_at.asc())
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all(), total


def create_ticket_field_value(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateTicketFieldValue | AdminCreateTicketFieldValue,
    created_by: str,
) -> TicketFieldValue:
    """Create a new ticket field value and publish a created event."""
    logger.debug(
        "Creating ticket field value: tenant_id=%s, ticket_id=%s, field_def_id=%s",
        tenant_id,
        ticket_id,
        request.ticket_field_def_id,
    )
    val = TicketFieldValue(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_field_def_id=request.ticket_field_def_id,
        value_text=request.value_text,
        value_number=request.value_number,
        value_bool=request.value_bool,
        value_date=request.value_date,
        value_ts=request.value_ts,
        value_json=request.value_json,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(val)
    commit_or_raise(db, refresh=val, action="create ticket field value")
    snapshot = _snapshot(val)
    TicketFieldValueProducer.send_ticket_field_value_created(
        tenant_id=tenant_id, payload=snapshot
    )
    return val


def get_ticket_field_value(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    value_id: uuid.UUID,
) -> TicketFieldValue:
    """Retrieve a ticket field value by ID within a tenant and ticket context."""
    val = (
        db.query(TicketFieldValue)
        .filter(
            TicketFieldValue.id == value_id,
            TicketFieldValue.tenant_id == tenant_id,
            TicketFieldValue.ticket_id == ticket_id,
        )
        .first()
    )
    if not val:
        logger.info(
            "Ticket field value not found: tenant_id=%s, ticket_id=%s, value_id=%s",
            tenant_id,
            ticket_id,
            value_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket field value not found"
        )
    return val


def update_ticket_field_value(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    value_id: uuid.UUID,
    request: TicketFieldValueUpdate,
    updated_by: str,
) -> TicketFieldValue:
    """Update an existing ticket field value and publish an update event."""
    val = get_ticket_field_value(
        db, tenant_id=tenant_id, ticket_id=ticket_id, value_id=value_id
    )
    updates: Dict[str, Any] = {}
    for field in [
        "value_text",
        "value_number",
        "value_bool",
        "value_date",
        "value_ts",
        "value_json",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(val, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(val, field, value)
        val.updated_by = updated_by
        val.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=val, action="update ticket field value")
        snapshot = _snapshot(val)
        TicketFieldValueProducer.send_ticket_field_value_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return val


def delete_ticket_field_value(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    value_id: uuid.UUID,
) -> None:
    """Delete a ticket field value and publish a deletion event."""
    val = get_ticket_field_value(
        db, tenant_id=tenant_id, ticket_id=ticket_id, value_id=value_id
    )
    db.delete(val)
    commit_or_raise(db, action="delete ticket field value")
    deleted_dt = datetime.utcnow().isoformat()
    TicketFieldValueProducer.send_ticket_field_value_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_ticket_field_values",
    "create_ticket_field_value",
    "get_ticket_field_value",
    "update_ticket_field_value",
    "delete_ticket_field_value",
]