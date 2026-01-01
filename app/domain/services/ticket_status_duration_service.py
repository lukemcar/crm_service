"""
Service layer for TicketStatusDuration entities.

This module provides CRUD operations for ticket status duration facts,
enforcing tenant scoping and publishing domain events upon successful
mutations.  Listing operations support optional filtering by ticket
and status and pagination.  Tenant APIs expose read‑only access to
these records; admin APIs may create, update, and delete them for
backfilling or manual corrections.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_status_duration import TicketStatusDuration
from app.domain.schemas.ticket_status_duration import (
    AdminCreateTicketStatusDuration,
    AdminUpdateTicketStatusDuration,
)
from app.domain.schemas.events.ticket_status_duration_event import (
    TicketStatusDurationDelta,
)
from app.messaging.producers.ticket_status_duration_producer import (
    TicketStatusDurationMessageProducer as TicketStatusDurationProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_status_duration_service")


def _snapshot(duration: TicketStatusDuration) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketStatusDuration for events."""
    return {
        "id": duration.id,
        "tenant_id": duration.tenant_id,
        "ticket_id": duration.ticket_id,
        "status": duration.status,
        "started_at": duration.started_at.isoformat() if duration.started_at else None,
        "ended_at": duration.ended_at.isoformat() if duration.ended_at else None,
        "duration_seconds": duration.duration_seconds,
        "created_at": duration.created_at.isoformat() if duration.created_at else None,
        "created_by": duration.created_by,
    }


def _compute_delta(duration: TicketStatusDuration, updates: Dict[str, Any]) -> TicketStatusDurationDelta:
    """Compute a delta for modified base fields on a TicketStatusDuration record."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(duration, field)
        # Compare datetimes by ISO string representation
        if isinstance(current, datetime):
            current_val = current.isoformat()
            new_val = value.isoformat() if isinstance(value, datetime) else value
        else:
            current_val = current
            new_val = value
        if current_val != new_val:
            changed[field] = value
    return TicketStatusDurationDelta(base_fields=changed or None)


def list_ticket_status_durations(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketStatusDuration], int]:
    """List ticket status durations for a tenant with optional filtering.

    Returns a tuple of the list of records and the total count.  Records
    are ordered by ``started_at`` ascending.
    """
    logger.debug(
        "Listing status durations: tenant_id=%s, ticket_id=%s, status=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        status,
        limit,
        offset,
    )
    query = db.query(TicketStatusDuration).filter(
        TicketStatusDuration.tenant_id == tenant_id
    )
    if ticket_id:
        query = query.filter(TicketStatusDuration.ticket_id == ticket_id)
    if status:
        query = query.filter(TicketStatusDuration.status == status)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketStatusDuration.started_at.asc())
    return query.all(), total


def create_ticket_status_duration(
    db: Session,
    *,
    request: AdminCreateTicketStatusDuration,
    created_by: str,
) -> TicketStatusDuration:
    """Create a new ticket status duration record and publish a created event."""
    logger.debug(
        "Creating ticket status duration: tenant_id=%s, ticket_id=%s, status=%s",
        request.tenant_id,
        request.ticket_id,
        request.status,
    )
    duration = TicketStatusDuration(
        tenant_id=request.tenant_id,
        ticket_id=request.ticket_id,
        status=request.status,
        started_at=request.started_at,
        ended_at=request.ended_at,
        duration_seconds=request.duration_seconds,
        created_by=created_by,
    )
    db.add(duration)
    commit_or_raise(db, refresh=duration, action="create ticket status duration")
    snapshot = _snapshot(duration)
    TicketStatusDurationProducer.send_ticket_status_duration_created(
        tenant_id=request.tenant_id, payload=snapshot
    )
    return duration


def get_ticket_status_duration(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    duration_id: uuid.UUID,
) -> TicketStatusDuration:
    """Retrieve a ticket status duration record by ID within a tenant context."""
    duration = (
        db.query(TicketStatusDuration)
        .filter(
            TicketStatusDuration.id == duration_id,
            TicketStatusDuration.tenant_id == tenant_id,
        )
        .first()
    )
    if not duration:
        logger.info(
            "Ticket status duration not found: tenant_id=%s, id=%s", tenant_id, duration_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket status duration not found")
    return duration


def update_ticket_status_duration(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    duration_id: uuid.UUID,
    request: AdminUpdateTicketStatusDuration,
    updated_by: str,
) -> TicketStatusDuration:
    """Update an existing ticket status duration record and publish an updated event."""
    duration = get_ticket_status_duration(db, tenant_id=tenant_id, duration_id=duration_id)
    updates: Dict[str, Any] = {}
    if request.status is not None:
        updates["status"] = request.status
    if request.started_at is not None:
        updates["started_at"] = request.started_at
    if request.ended_at is not None:
        updates["ended_at"] = request.ended_at
    if request.duration_seconds is not None:
        updates["duration_seconds"] = request.duration_seconds
    if not updates:
        return duration
    delta = _compute_delta(duration, updates)
    for field, value in updates.items():
        setattr(duration, field, value)
    # update created_by? do not change created_by; update created_at? not needed; set new created_by? but we store updated by maybe; we choose to not track updated_by for status durations; events rely on updated_by only in payload? We'll not include.
    commit_or_raise(db, refresh=duration, action="update ticket status duration")
    snapshot = _snapshot(duration)
    TicketStatusDurationProducer.send_ticket_status_duration_updated(
        tenant_id=tenant_id, changes=delta, payload=snapshot
    )
    return duration


def delete_ticket_status_duration(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    duration_id: uuid.UUID,
) -> None:
    """Delete a status duration record and publish a deleted event."""
    duration = get_ticket_status_duration(db, tenant_id=tenant_id, duration_id=duration_id)
    db.delete(duration)
    commit_or_raise(db, action="delete ticket status duration")
    deleted_dt = datetime.utcnow().isoformat()
    TicketStatusDurationProducer.send_ticket_status_duration_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None