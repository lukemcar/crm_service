"""
Service layer for TicketTaskMirror entities.

This module provides operations to list, retrieve and upsert ticket task
mirrors. Task mirrors are read-only for tenants; only admin/internal
operations can create or update them. Each mutation publishes an event
via the TicketTaskMirrorMessageProducer.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_task_mirror import TicketTaskMirror
from app.domain.schemas.ticket_task_mirror import AdminUpsertTicketTaskMirror
from app.domain.schemas.events.ticket_task_mirror_event import (
    TicketTaskMirrorDelta,
)
from app.messaging.producers.ticket_task_mirror_producer import (
    TicketTaskMirrorMessageProducer as Producer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_task_mirror_service")


def _snapshot(mirror: TicketTaskMirror) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketTaskMirror for event payloads."""
    return {
        "id": mirror.id,
        "tenant_id": mirror.tenant_id,
        "ticket_id": mirror.ticket_id,
        "orchestration_task_id": mirror.orchestration_task_id,
        "orchestration_process_instance_id": mirror.orchestration_process_instance_id,
        "orchestration_process_definition_key": mirror.orchestration_process_definition_key,
        "name": mirror.name,
        "description": mirror.description,
        "status": mirror.status,
        "due_at": mirror.due_at.isoformat() if mirror.due_at else None,
        "assigned_user_id": mirror.assigned_user_id,
        "assigned_group_id": mirror.assigned_group_id,
        "created_at": mirror.created_at.isoformat() if mirror.created_at else None,
        "updated_at": mirror.updated_at.isoformat() if mirror.updated_at else None,
    }


def _compute_delta(mirror: TicketTaskMirror, updates: Dict[str, Any]) -> TicketTaskMirrorDelta:
    """Compute a delta object for modified base fields on a task mirror."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(mirror, field)
        # When comparing datetimes, convert to iso strings for equality check
        if isinstance(value, datetime):
            current_iso = current.isoformat() if current else None
            if current_iso != value.isoformat():
                changed[field] = value
        else:
            if current != value:
                changed[field] = value
    return TicketTaskMirrorDelta(base_fields=changed or None)


def list_ticket_task_mirrors(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketTaskMirror], int]:
    """List ticket task mirrors for a tenant with optional filtering by ticket and status."""
    logger.debug(
        "Listing task mirrors: tenant_id=%s, ticket_id=%s, status=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        status,
        limit,
        offset,
    )
    query = db.query(TicketTaskMirror).filter(TicketTaskMirror.tenant_id == tenant_id)
    if ticket_id:
        query = query.filter(TicketTaskMirror.ticket_id == ticket_id)
    if status:
        query = query.filter(TicketTaskMirror.status == status)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketTaskMirror.created_at.desc())
    return query.all(), total


def get_ticket_task_mirror(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    mirror_id: uuid.UUID,
) -> TicketTaskMirror:
    """Retrieve a task mirror by ID within a tenant context."""
    mirror = (
        db.query(TicketTaskMirror)
        .filter(
            TicketTaskMirror.id == mirror_id,
            TicketTaskMirror.tenant_id == tenant_id,
        )
        .first()
    )
    if not mirror:
        logger.info(
            "Ticket task mirror not found: tenant_id=%s, mirror_id=%s",
            tenant_id,
            mirror_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket task mirror not found"
        )
    return mirror


def upsert_ticket_task_mirror(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: AdminUpsertTicketTaskMirror,
    updated_by: str,
) -> TicketTaskMirror:
    """Create or update a ticket task mirror within a tenant context.

    If a record with the same ``id`` exists, its fields are updated. If the
    ``id`` is omitted or does not exist, a new record is created. The
    function publishes created or updated events accordingly.
    """
    mirror: Optional[TicketTaskMirror] = None
    if request.id:
        mirror = (
            db.query(TicketTaskMirror)
            .filter(
                TicketTaskMirror.id == request.id,
                TicketTaskMirror.tenant_id == tenant_id,
            )
            .first()
        )
    creating = mirror is None
    # Prepare due_at datetime from ISO string if provided
    due_dt: Optional[datetime] = None
    if request.due_at:
        try:
            due_dt = datetime.fromisoformat(request.due_at)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid ISO format for due_at",
            )
    if creating:
        # Create new record
        new_id = request.id or uuid.uuid4()
        mirror = TicketTaskMirror(
            id=new_id,
            tenant_id=tenant_id,
            ticket_id=request.ticket_id,
            orchestration_task_id=request.orchestration_task_id,
            orchestration_process_instance_id=request.orchestration_process_instance_id,
            orchestration_process_definition_key=request.orchestration_process_definition_key,
            name=request.name,
            description=request.description,
            status=request.status or "open",
            due_at=due_dt,
            assigned_user_id=request.assigned_user_id,
            assigned_group_id=request.assigned_group_id,
        )
        db.add(mirror)
        # created_by and updated_by not stored on mirror (no created_by field)
        commit_or_raise(db, refresh=mirror, action="create ticket task mirror")
        snapshot = _snapshot(mirror)
        Producer.send_ticket_task_mirror_created(tenant_id=tenant_id, payload=snapshot)
        return mirror
    # Else update existing
    updates: Dict[str, Any] = {}
    # Determine fields to update
    for field in [
        "orchestration_process_instance_id",
        "orchestration_process_definition_key",
        "name",
        "description",
        "status",
        "assigned_user_id",
        "assigned_group_id",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    # Due_at separate
    if due_dt is not None:
        updates["due_at"] = due_dt
    delta = _compute_delta(mirror, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(mirror, field, value)
        mirror.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=mirror, action="update ticket task mirror")
        snapshot = _snapshot(mirror)
        Producer.send_ticket_task_mirror_updated(
            tenant_id=tenant_id,
            delta=delta,
            payload=snapshot,
        )
    return mirror


def delete_ticket_task_mirror(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    mirror_id: uuid.UUID,
) -> None:
    """Delete a ticket task mirror and publish a deletion event."""
    mirror = get_ticket_task_mirror(db, tenant_id=tenant_id, mirror_id=mirror_id)
    payload = _snapshot(mirror)
    db.delete(mirror)
    commit_or_raise(db, action="delete ticket task mirror")
    Producer.send_ticket_task_mirror_deleted(tenant_id=tenant_id, payload=payload)
    return None


__all__ = [
    "list_ticket_task_mirrors",
    "get_ticket_task_mirror",
    "upsert_ticket_task_mirror",
    "delete_ticket_task_mirror",
]