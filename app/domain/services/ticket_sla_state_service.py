"""
Service layer for TicketSlaState entities.

This module provides read and update operations for ticket SLA state.
Ticket SLA state records computed deadlines and breach indicators for
tickets.  Tenant and admin users may list and retrieve state records.
Admin/internal users may update state to reflect recalculated
deadlines.  Update operations emit domain events upon successful
mutation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_sla_state import TicketSlaState
from app.domain.schemas.ticket_sla_state import TicketSlaStateUpdate
from app.domain.schemas.events.ticket_sla_state_event import TicketSlaStateDelta
from app.messaging.producers.ticket_sla_state_producer import (
    TicketSlaStateMessageProducer as TicketSlaStateProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_sla_state_service")


def _snapshot(state: TicketSlaState) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketSlaState suitable for event payloads."""
    return {
        "id": state.id,
        "tenant_id": state.tenant_id,
        "ticket_id": state.ticket_id,
        "sla_policy_id": state.sla_policy_id,
        "first_response_due_at": state.first_response_due_at.isoformat() if state.first_response_due_at else None,
        "next_response_due_at": state.next_response_due_at.isoformat() if state.next_response_due_at else None,
        "resolution_due_at": state.resolution_due_at.isoformat() if state.resolution_due_at else None,
        "first_response_breached": state.first_response_breached,
        "next_response_breached": state.next_response_breached,
        "resolution_breached": state.resolution_breached,
        "last_computed_at": state.last_computed_at.isoformat() if state.last_computed_at else None,
        "created_at": state.created_at.isoformat() if state.created_at else None,
        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        "created_by": state.created_by,
        "updated_by": state.updated_by,
    }


def _compute_delta(state: TicketSlaState, updates: Dict[str, Any]) -> TicketSlaStateDelta:
    """Compute a delta object for modified fields on a ticket SLA state."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        # Skip None values; only record actual changes
        if value is None:
            continue
        current = getattr(state, field)
        # For datetime strings, we convert to isoformat to compare easily
        if isinstance(current, datetime):
            current_val: Any = current.isoformat()
        else:
            current_val = current
        if current_val != value:
            changed[field] = value
    return TicketSlaStateDelta(base_fields=changed or None)


def list_ticket_sla_states(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: Optional[uuid.UUID] = None,
    sla_policy_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketSlaState], int]:
    """List ticket SLA states with optional filtering by ticket or policy."""
    logger.debug(
        "Listing ticket SLA states: tenant_id=%s, ticket_id=%s, sla_policy_id=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        sla_policy_id,
        limit,
        offset,
    )
    query = db.query(TicketSlaState).filter(TicketSlaState.tenant_id == tenant_id)
    if ticket_id:
        query = query.filter(TicketSlaState.ticket_id == ticket_id)
    if sla_policy_id:
        query = query.filter(TicketSlaState.sla_policy_id == sla_policy_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketSlaState.last_computed_at.desc())
    return query.all(), total


def get_ticket_sla_state(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    state_id: uuid.UUID,
) -> TicketSlaState:
    """Retrieve a ticket SLA state by ID within a tenant context."""
    state = (
        db.query(TicketSlaState)
        .filter(
            TicketSlaState.id == state_id,
            TicketSlaState.tenant_id == tenant_id,
        )
        .first()
    )
    if not state:
        logger.info(
            "Ticket SLA state not found: tenant_id=%s, state_id=%s", tenant_id, state_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket SLA state not found")
    return state


def update_ticket_sla_state(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TicketSlaStateUpdate,
    updated_by: str,
) -> TicketSlaState:
    """Update an existing ticket SLA state and publish an update event."""
    # Retrieve by tenant_id and ticket_id
    state = (
        db.query(TicketSlaState)
        .filter(
            TicketSlaState.tenant_id == tenant_id,
            TicketSlaState.ticket_id == ticket_id,
        )
        .first()
    )
    if not state:
        logger.info(
            "Ticket SLA state not found for update: tenant_id=%s, ticket_id=%s", tenant_id, ticket_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket SLA state not found")
    # Convert ISO strings to datetime objects for due dates and last_computed_at
    updates: Dict[str, Any] = {}
    if request.sla_policy_id is not None:
        updates["sla_policy_id"] = request.sla_policy_id
    for field in [
        "first_response_due_at",
        "next_response_due_at",
        "resolution_due_at",
        "last_computed_at",
    ]:
        value = getattr(request, field)
        if value is not None:
            try:
                # parse ISO string to datetime
                parsed = datetime.fromisoformat(value)  # type: ignore[arg-type]
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid ISO datetime for {field}")
            updates[field] = parsed
    for field in [
        "first_response_breached",
        "next_response_breached",
        "resolution_breached",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(state, {
        **{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in updates.items()},
    })
    if delta.base_fields:
        # Apply updates
        for field, value in updates.items():
            setattr(state, field, value)
        state.updated_by = updated_by
        state.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=state, action="update ticket SLA state")
        snapshot = _snapshot(state)
        TicketSlaStateProducer.send_ticket_sla_state_updated(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            changes=delta,
            payload=snapshot,
        )
    return state


__all__ = [
    "list_ticket_sla_states",
    "get_ticket_sla_state",
    "update_ticket_sla_state",
]
