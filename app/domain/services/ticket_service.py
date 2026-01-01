"""
Service layer for Ticket entities.

This module implements CRUD operations for tickets.  Tickets are
created and updated in a tenant context; admin operations allow
cross‑tenant management.  Listing operations support optional
filters on status, priority and assignee.  After successful
mutations, domain events are published via the ticket message
producer.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket import Ticket
from app.domain.schemas.ticket import (
    TenantCreateTicket,
    AdminCreateTicket,
    TicketUpdate,
)
from app.domain.schemas.events.ticket_event import TicketDelta
from app.messaging.producers.ticket_producer import TicketMessageProducer as TicketProducer
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_service")


def _snapshot(ticket: Ticket) -> Dict[str, Any]:
    """Return a dictionary representation of a Ticket suitable for event payloads."""
    return {
        "id": ticket.id,
        "tenant_id": ticket.tenant_id,
        "requester_contact_id": ticket.requester_contact_id,
        "company_id": ticket.company_id,
        "inbound_channel_id": ticket.inbound_channel_id,
        "ticket_form_id": ticket.ticket_form_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "ticket_type": ticket.ticket_type,
        "assigned_group_id": ticket.assigned_group_id,
        "assigned_user_id": ticket.assigned_user_id,
        "first_response_at": ticket.first_response_at.isoformat() if ticket.first_response_at else None,
        "last_message_at": ticket.last_message_at.isoformat() if ticket.last_message_at else None,
        "solved_at": ticket.solved_at.isoformat() if ticket.solved_at else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "custom_fields": ticket.custom_fields,
        "orchestration_workflow_key": ticket.orchestration_workflow_key,
        "orchestration_instance_id": ticket.orchestration_instance_id,
        "orchestration_state": ticket.orchestration_state,
        "work_mode": ticket.work_mode,
        "ai_status": ticket.ai_status,
        "ai_last_session_id": ticket.ai_last_session_id,
        "ai_last_agent_key": ticket.ai_last_agent_key,
        "ai_last_outcome": ticket.ai_last_outcome,
        "ai_last_confidence": float(ticket.ai_last_confidence) if ticket.ai_last_confidence is not None else None,
        "ai_last_completed_at": ticket.ai_last_completed_at.isoformat() if ticket.ai_last_completed_at else None,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        "created_by": ticket.created_by,
        "updated_by": ticket.updated_by,
    }


def _compute_delta(ticket: Ticket, updates: Dict[str, Any]) -> TicketDelta:
    """Compute a delta object for modified base fields on a ticket."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(ticket, field)
        if current != value:
            changed[field] = value
    return TicketDelta(base_fields=changed or None)


def list_tickets(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_user_id: Optional[uuid.UUID] = None,
    assigned_group_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[Ticket], int]:
    """List tickets with optional filtering.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Additional filters may include status, priority, assigned user or group.
    Results are ordered by creation date descending and can be paginated.
    Returns the list of tickets and the total count.
    """
    logger.debug(
        "Listing tickets: tenant_id=%s, status=%s, priority=%s, assigned_user_id=%s, assigned_group_id=%s, limit=%s, offset=%s",
        tenant_id,
        status,
        priority,
        assigned_user_id,
        assigned_group_id,
        limit,
        offset,
    )
    query = db.query(Ticket)
    if tenant_id:
        query = query.filter(Ticket.tenant_id == tenant_id)
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if assigned_user_id:
        query = query.filter(Ticket.assigned_user_id == assigned_user_id)
    if assigned_group_id:
        query = query.filter(Ticket.assigned_group_id == assigned_group_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(Ticket.created_at.desc())
    return query.all(), total


def create_ticket(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateTicket | AdminCreateTicket,
    created_by: str,
) -> Ticket:
    """Create a ticket and publish a created event."""
    logger.debug(
        "Creating ticket: tenant_id=%s, subject=%s",
        tenant_id,
        request.subject,
    )
    ticket = Ticket(
        tenant_id=tenant_id,
        requester_contact_id=getattr(request, "requester_contact_id", None),
        company_id=getattr(request, "company_id", None),
        inbound_channel_id=request.inbound_channel_id,
        ticket_form_id=request.ticket_form_id,
        subject=request.subject,
        description=request.description,
        status=request.status or "new",
        priority=request.priority or "normal",
        ticket_type=request.ticket_type or "question",
        assigned_group_id=request.assigned_group_id,
        assigned_user_id=request.assigned_user_id,
        custom_fields=request.custom_fields,
        work_mode=request.work_mode or "human_only",
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(ticket)
    commit_or_raise(db, refresh=ticket, action="create ticket")
    snapshot = _snapshot(ticket)
    TicketProducer.send_ticket_created(tenant_id=tenant_id, payload=snapshot)
    return ticket


def get_ticket(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
) -> Ticket:
    """Retrieve a ticket by ID within a tenant context."""
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.tenant_id == tenant_id)
        .first()
    )
    if not ticket:
        logger.info(
            "Ticket not found: tenant_id=%s, ticket_id=%s", tenant_id, ticket_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def update_ticket(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TicketUpdate,
    updated_by: str,
) -> Ticket:
    """Update an existing ticket and publish an update event."""
    ticket = get_ticket(db, tenant_id=tenant_id, ticket_id=ticket_id)
    updates: Dict[str, Any] = {}
    for field in [
        "subject",
        "description",
        "status",
        "priority",
        "ticket_type",
        "assigned_group_id",
        "assigned_user_id",
        "inbound_channel_id",
        "ticket_form_id",
        "custom_fields",
        "work_mode",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(ticket, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(ticket, field, value)
        ticket.updated_by = updated_by
        ticket.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=ticket, action="update ticket")
        snapshot = _snapshot(ticket)
        TicketProducer.send_ticket_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return ticket


def delete_ticket(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
) -> None:
    """Delete a ticket and publish a deletion event."""
    ticket = get_ticket(db, tenant_id=tenant_id, ticket_id=ticket_id)
    db.delete(ticket)
    commit_or_raise(db, action="delete ticket")
    deleted_dt = datetime.utcnow().isoformat()
    TicketProducer.send_ticket_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_tickets",
    "create_ticket",
    "get_ticket",
    "update_ticket",
    "delete_ticket",
]