"""
Service layer for TicketForm entities.

This module provides CRUD operations for ticket forms, ensuring
tenant scoping and emitting domain events upon successful mutations.
Listing operations support optional filtering by active status.  Unique
constraints and check constraints are enforced at the database layer;
violations will surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_form import TicketForm
from app.domain.schemas.ticket_form import (
    TicketFormUpdate,
    TenantCreateTicketForm,
    AdminCreateTicketForm,
)
from app.domain.schemas.events.ticket_form_event import TicketFormDelta
from app.messaging.producers.ticket_form_producer import (
    TicketFormMessageProducer as TicketFormProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_form_service")


def _snapshot(form: TicketForm) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketForm suitable for event payloads."""
    return {
        "id": form.id,
        "tenant_id": form.tenant_id,
        "name": form.name,
        "description": form.description,
        "is_active": form.is_active,
        "created_at": form.created_at.isoformat() if form.created_at else None,
        "updated_at": form.updated_at.isoformat() if form.updated_at else None,
        "created_by": form.created_by,
        "updated_by": form.updated_by,
    }


def _compute_delta(form: TicketForm, updates: Dict[str, Any]) -> TicketFormDelta:
    """Compute a delta object for modified base fields on a ticket form."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        # Skip None values; only record actual changes
        if value is None:
            continue
        current = getattr(form, field)
        # Basic comparison suffices for simple fields
        if current != value:
            changed[field] = value
    return TicketFormDelta(base_fields=changed or None)


def list_ticket_forms(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketForm], int]:
    """List ticket forms with optional filtering by active status and tenant.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``is_active`` filters forms by activation status.  Results are ordered by
    creation time descending and can be paginated via ``limit`` and
    ``offset``.  Returns the list of forms and the total count.
    """
    logger.debug(
        "Listing ticket forms: tenant_id=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        is_active,
        limit,
        offset,
    )
    query = db.query(TicketForm)
    if tenant_id:
        query = query.filter(TicketForm.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(TicketForm.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketForm.created_at.desc())
    return query.all(), total


def create_ticket_form(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateTicketForm | AdminCreateTicketForm,
    created_by: str,
) -> TicketForm:
    """Create a new ticket form and publish a created event."""
    logger.debug(
        "Creating ticket form: tenant_id=%s, name=%s",
        tenant_id,
        request.name,
    )
    # Determine activation status; default to True if not explicitly provided
    is_active = request.is_active if request.is_active is not None else True
    form = TicketForm(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        is_active=is_active,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(form)
    commit_or_raise(db, refresh=form, action="create ticket form")
    snapshot = _snapshot(form)
    TicketFormProducer.send_ticket_form_created(tenant_id=tenant_id, payload=snapshot)
    return form


def get_ticket_form(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
) -> TicketForm:
    """Retrieve a ticket form by ID within a tenant context."""
    form = (
        db.query(TicketForm)
        .filter(
            TicketForm.id == form_id,
            TicketForm.tenant_id == tenant_id,
        )
        .first()
    )
    if not form:
        logger.info(
            "Ticket form not found: tenant_id=%s, form_id=%s", tenant_id, form_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket form not found")
    return form


def update_ticket_form(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
    request: TicketFormUpdate,
    updated_by: str,
) -> TicketForm:
    """Update an existing ticket form and publish an update event."""
    form = get_ticket_form(db, tenant_id=tenant_id, form_id=form_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "description", "is_active"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(form, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(form, field, value)
        form.updated_by = updated_by
        form.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=form, action="update ticket form")
        snapshot = _snapshot(form)
        TicketFormProducer.send_ticket_form_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return form


def delete_ticket_form(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
) -> None:
    """Delete a ticket form and publish a deletion event."""
    form = get_ticket_form(db, tenant_id=tenant_id, form_id=form_id)
    db.delete(form)
    commit_or_raise(db, action="delete ticket form")
    deleted_dt = datetime.utcnow().isoformat()
    TicketFormProducer.send_ticket_form_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_ticket_forms",
    "create_ticket_form",
    "get_ticket_form",
    "update_ticket_form",
    "delete_ticket_form",
]