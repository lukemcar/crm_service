"""Service layer for TicketTimeEntry entities.

This module provides CRUD operations for ticket time entries, ensuring
tenant scoping and emitting domain events upon successful mutations.
Listing operations support optional filtering by user or work type and
pagination. Unique and check constraints are enforced at the database
layer; violations will surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_time_entry import TicketTimeEntry
from app.domain.schemas.ticket_time_entry import (
    TicketTimeEntryUpdate,
    TenantCreateTicketTimeEntry,
    AdminCreateTicketTimeEntry,
)
from app.domain.schemas.events.ticket_time_entry_event import TicketTimeEntryDelta
from app.messaging.producers.ticket_time_entry_producer import (
    TicketTimeEntryMessageProducer as TicketTimeEntryProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_time_entry_service")


def _snapshot(entry: TicketTimeEntry) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketTimeEntry suitable for event payloads."""
    return {
        "id": entry.id,
        "tenant_id": entry.tenant_id,
        "ticket_id": entry.ticket_id,
        "user_id": entry.user_id,
        "minutes_spent": entry.minutes_spent,
        "work_type": entry.work_type,
        "note": entry.note,
        "started_at": entry.started_at.isoformat() if entry.started_at else None,
        "ended_at": entry.ended_at.isoformat() if entry.ended_at else None,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "created_by": entry.created_by,
    }


def _compute_delta(entry: TicketTimeEntry, updates: Dict[str, Any]) -> TicketTimeEntryDelta:
    """Compute a delta object for modified base fields on a time entry."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(entry, field)
        # Compare values; for datetimes convert to ISO strings for equality
        if isinstance(current, datetime):
            current_val = current.isoformat()
        else:
            current_val = current
        new_val = value.isoformat() if isinstance(value, datetime) else value
        if current_val != new_val:
            changed[field] = value
    return TicketTimeEntryDelta(base_fields=changed or None)


def list_ticket_time_entries(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    work_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketTimeEntry], int]:
    """List time entries for a ticket with optional filtering by user and work type.

    Returns a tuple of the list of entries and the total count. Entries are ordered
    by creation time ascending (chronological order).
    """
    logger.debug(
        "Listing time entries: tenant_id=%s, ticket_id=%s, user_id=%s, work_type=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        user_id,
        work_type,
        limit,
        offset,
    )
    query = db.query(TicketTimeEntry).filter(
        TicketTimeEntry.tenant_id == tenant_id,
        TicketTimeEntry.ticket_id == ticket_id,
    )
    if user_id:
        query = query.filter(TicketTimeEntry.user_id == user_id)
    if work_type:
        query = query.filter(TicketTimeEntry.work_type == work_type)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketTimeEntry.created_at.asc())
    return query.all(), total


def create_ticket_time_entry(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateTicketTimeEntry | AdminCreateTicketTimeEntry,
    created_by: str,
) -> TicketTimeEntry:
    """Create a new time entry and publish a created event."""
    logger.debug(
        "Creating time entry: tenant_id=%s, ticket_id=%s, minutes=%s",
        tenant_id,
        ticket_id,
        request.minutes_spent,
    )
    # Parse ISO timestamps if provided
    def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
        if ts is None:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid datetime format: {ts}",
            )

    started_at = _parse_iso(request.started_at) if hasattr(request, "started_at") else None
    ended_at = _parse_iso(request.ended_at) if hasattr(request, "ended_at") else None
    entry = TicketTimeEntry(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        user_id=request.user_id,
        minutes_spent=request.minutes_spent,
        work_type=request.work_type,
        note=request.note,
        started_at=started_at,
        ended_at=ended_at,
        created_by=created_by,
    )
    db.add(entry)
    commit_or_raise(db, refresh=entry, action="create ticket time entry")
    snapshot = _snapshot(entry)
    TicketTimeEntryProducer.send_ticket_time_entry_created(
        tenant_id=tenant_id, payload=snapshot
    )
    return entry


def get_ticket_time_entry(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    time_entry_id: uuid.UUID,
) -> TicketTimeEntry:
    """Retrieve a time entry by ID within a tenant context."""
    entry = (
        db.query(TicketTimeEntry)
        .filter(
            TicketTimeEntry.id == time_entry_id,
            TicketTimeEntry.tenant_id == tenant_id,
        )
        .first()
    )
    if not entry:
        logger.info(
            "Time entry not found: tenant_id=%s, id=%s", tenant_id, time_entry_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found")
    return entry


def update_ticket_time_entry(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    time_entry_id: uuid.UUID,
    request: TicketTimeEntryUpdate,
    updated_by: str,
) -> TicketTimeEntry:
    """Update an existing time entry and publish an update event."""
    entry = get_ticket_time_entry(db, tenant_id=tenant_id, time_entry_id=time_entry_id)
    updates: Dict[str, Any] = {}
    # Parse ISO strings to datetimes
    def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
        if ts is None:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid datetime format: {ts}",
            )

    if request.minutes_spent is not None:
        updates["minutes_spent"] = request.minutes_spent
    if request.user_id is not None:
        updates["user_id"] = request.user_id
    if request.work_type is not None:
        updates["work_type"] = request.work_type
    if request.note is not None:
        updates["note"] = request.note
    if request.started_at is not None:
        updates["started_at"] = _parse_iso(request.started_at)
    if request.ended_at is not None:
        updates["ended_at"] = _parse_iso(request.ended_at)
    delta = _compute_delta(entry, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(entry, field, value)
        # Note: only created_at/created_by fields exist on this model; no updated_at
        # We do not track updated_by/time as there is no separate updated fields on the model.
        commit_or_raise(db, refresh=entry, action="update ticket time entry")
        snapshot = _snapshot(entry)
        TicketTimeEntryProducer.send_ticket_time_entry_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return entry


def delete_ticket_time_entry(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    time_entry_id: uuid.UUID,
) -> None:
    """Delete a time entry and publish a deletion event."""
    entry = get_ticket_time_entry(db, tenant_id=tenant_id, time_entry_id=time_entry_id)
    db.delete(entry)
    commit_or_raise(db, action="delete ticket time entry")
    deleted_dt = datetime.utcnow().isoformat()
    TicketTimeEntryProducer.send_ticket_time_entry_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_ticket_time_entries",
    "create_ticket_time_entry",
    "get_ticket_time_entry",
    "update_ticket_time_entry",
    "delete_ticket_time_entry",
]