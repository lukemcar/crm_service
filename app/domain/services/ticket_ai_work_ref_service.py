"""
Service layer for TicketAiWorkRef entities.

This module provides operations to list, retrieve and upsert AI work
references associated with tickets. These records are read-only for
tenants; admin/internal operations can create or update them. Each
mutation publishes an event via the TicketAiWorkRefMessageProducer.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_ai_work_ref import TicketAiWorkRef
from app.domain.schemas.ticket_ai_work_ref import AdminUpsertTicketAiWorkRef
from app.domain.schemas.events.ticket_ai_work_ref_event import TicketAiWorkRefDelta
from app.messaging.producers.ticket_ai_work_ref_producer import (
    TicketAiWorkRefMessageProducer as Producer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_ai_work_ref_service")


def _snapshot(ref: TicketAiWorkRef) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketAiWorkRef for event payloads."""
    return {
        "id": ref.id,
        "tenant_id": ref.tenant_id,
        "ticket_id": ref.ticket_id,
        "ai_session_id": ref.ai_session_id,
        "agent_key": ref.agent_key,
        "purpose": ref.purpose,
        "status": ref.status,
        "outcome": ref.outcome,
        "confidence": float(ref.confidence) if ref.confidence is not None else None,
        "requested_at": ref.requested_at.isoformat() if ref.requested_at else None,
        "completed_at": ref.completed_at.isoformat() if ref.completed_at else None,
        "created_by": ref.created_by,
    }


def _compute_delta(ref: TicketAiWorkRef, updates: Dict[str, Any]) -> TicketAiWorkRefDelta:
    """Compute a delta object for modified base fields on an AI work ref."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(ref, field)
        # handle datetimes and numeric comparision
        if isinstance(value, datetime):
            current_iso = current.isoformat() if current else None
            if current_iso != value.isoformat():
                changed[field] = value
        elif isinstance(value, float):
            # convert Decimal or None to float for comparison
            current_float = float(current) if current is not None else None
            if current_float != value:
                changed[field] = value
        else:
            if current != value:
                changed[field] = value
    return TicketAiWorkRefDelta(base_fields=changed or None)


def list_ticket_ai_work_refs(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: Optional[uuid.UUID] = None,
    agent_key: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketAiWorkRef], int]:
    """List ticket AI work references for a tenant with optional filtering by ticket and agent."""
    logger.debug(
        "Listing AI work refs: tenant_id=%s, ticket_id=%s, agent_key=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        agent_key,
        limit,
        offset,
    )
    query = db.query(TicketAiWorkRef).filter(TicketAiWorkRef.tenant_id == tenant_id)
    if ticket_id:
        query = query.filter(TicketAiWorkRef.ticket_id == ticket_id)
    if agent_key:
        query = query.filter(TicketAiWorkRef.agent_key == agent_key)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketAiWorkRef.requested_at.desc())
    return query.all(), total


def get_ticket_ai_work_ref(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ref_id: uuid.UUID,
) -> TicketAiWorkRef:
    """Retrieve an AI work reference by ID within a tenant context."""
    ref = (
        db.query(TicketAiWorkRef)
        .filter(
            TicketAiWorkRef.id == ref_id,
            TicketAiWorkRef.tenant_id == tenant_id,
        )
        .first()
    )
    if not ref:
        logger.info(
            "Ticket AI work ref not found: tenant_id=%s, ref_id=%s",
            tenant_id,
            ref_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket AI work reference not found"
        )
    return ref


def upsert_ticket_ai_work_ref(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: AdminUpsertTicketAiWorkRef,
    updated_by: str,
) -> TicketAiWorkRef:
    """Create or update a ticket AI work reference within a tenant context.

    If a record with the same ``id`` exists, its fields are updated. If the
    ``id`` is omitted or does not exist, a new record is created.
    """
    ref: Optional[TicketAiWorkRef] = None
    if request.id:
        ref = (
            db.query(TicketAiWorkRef)
            .filter(
                TicketAiWorkRef.id == request.id,
                TicketAiWorkRef.tenant_id == tenant_id,
            )
            .first()
        )
    creating = ref is None
    requested_dt: Optional[datetime] = None
    completed_dt: Optional[datetime] = None
    # Parse ISO datetimes if provided
    if request.requested_at:
        try:
            requested_dt = datetime.fromisoformat(request.requested_at)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid ISO format for requested_at",
            )
    if request.completed_at:
        try:
            completed_dt = datetime.fromisoformat(request.completed_at)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid ISO format for completed_at",
            )
    if creating:
        new_id = request.id or uuid.uuid4()
        ref = TicketAiWorkRef(
            id=new_id,
            tenant_id=tenant_id,
            ticket_id=request.ticket_id,
            ai_session_id=request.ai_session_id,
            agent_key=request.agent_key,
            purpose=request.purpose,
            status=request.status or "started",
            outcome=request.outcome,
            confidence=request.confidence,
            requested_at=requested_dt or datetime.utcnow(),
            completed_at=completed_dt,
            created_by=request.created_by or updated_by,
        )
        db.add(ref)
        commit_or_raise(db, refresh=ref, action="create ticket AI work ref")
        snapshot = _snapshot(ref)
        Producer.send_ticket_ai_work_ref_created(tenant_id=tenant_id, payload=snapshot)
        return ref
    # Else update existing
    updates: Dict[str, Any] = {}
    for field in [
        "agent_key",
        "purpose",
        "status",
        "outcome",
        "confidence",
        "ticket_id",
        "ai_session_id",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    # requested_at/completed_at updates
    if requested_dt is not None:
        updates["requested_at"] = requested_dt
    if completed_dt is not None:
        updates["completed_at"] = completed_dt
    delta = _compute_delta(ref, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(ref, field, value)
        commit_or_raise(db, refresh=ref, action="update ticket AI work ref")
        snapshot = _snapshot(ref)
        Producer.send_ticket_ai_work_ref_updated(
            tenant_id=tenant_id,
            delta=delta,
            payload=snapshot,
        )
    return ref


def delete_ticket_ai_work_ref(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ref_id: uuid.UUID,
) -> None:
    """Delete a ticket AI work reference and publish a deletion event."""
    ref = get_ticket_ai_work_ref(db, tenant_id=tenant_id, ref_id=ref_id)
    payload = _snapshot(ref)
    db.delete(ref)
    commit_or_raise(db, action="delete ticket AI work ref")
    Producer.send_ticket_ai_work_ref_deleted(tenant_id=tenant_id, payload=payload)
    return None


__all__ = [
    "list_ticket_ai_work_refs",
    "get_ticket_ai_work_ref",
    "upsert_ticket_ai_work_ref",
    "delete_ticket_ai_work_ref",
]