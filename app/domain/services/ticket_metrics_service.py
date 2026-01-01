"""
Service layer for TicketMetrics entities.

This module provides CRUD operations for ticket metrics, enforcing
tenant scoping and publishing domain events after successful
database mutations.  Listing operations support optional filtering
by ticket and pagination.  This data is typically read‑only for
tenant APIs; admin APIs can create, update, and delete metrics
records.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_metrics import TicketMetrics
from app.domain.schemas.ticket_metrics import (
    AdminCreateTicketMetrics,
    TicketMetricsUpdate,
)
from app.domain.schemas.events.ticket_metrics_event import TicketMetricsDelta
from app.messaging.producers.ticket_metrics_producer import (
    TicketMetricsMessageProducer as TicketMetricsProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_metrics_service")


def _snapshot(metrics: TicketMetrics) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketMetrics for event payloads."""
    return {
        "id": metrics.id,
        "tenant_id": metrics.tenant_id,
        "ticket_id": metrics.ticket_id,
        "reply_count": metrics.reply_count,
        "reopen_count": metrics.reopen_count,
        "created_at": metrics.created_at.isoformat() if metrics.created_at else None,
        "updated_at": metrics.updated_at.isoformat() if metrics.updated_at else None,
        "updated_by": metrics.updated_by,
    }


def _compute_delta(metrics: TicketMetrics, updates: Dict[str, Any]) -> TicketMetricsDelta:
    """Compute a delta for modified base fields on a TicketMetrics record."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(metrics, field)
        if current != value:
            changed[field] = value
    return TicketMetricsDelta(base_fields=changed or None)


def list_ticket_metrics(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[TicketMetrics], int]:
    """List ticket metrics for a tenant with optional filtering by ticket.

    Returns a tuple of the list of metrics records and the total count.
    Records are ordered by updated_at descending.
    """
    logger.debug(
        "Listing ticket metrics: tenant_id=%s, ticket_id=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        limit,
        offset,
    )
    query = db.query(TicketMetrics).filter(TicketMetrics.tenant_id == tenant_id)
    if ticket_id:
        query = query.filter(TicketMetrics.ticket_id == ticket_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(TicketMetrics.updated_at.desc())
    return query.all(), total


def create_ticket_metrics(
    db: Session,
    *,
    request: AdminCreateTicketMetrics,
    created_by: str,
) -> TicketMetrics:
    """Create a new metrics record and publish a created event."""
    logger.debug(
        "Creating ticket metrics: tenant_id=%s, ticket_id=%s, reply_count=%s, reopen_count=%s",
        request.tenant_id,
        request.ticket_id,
        request.reply_count,
        request.reopen_count,
    )
    metrics = TicketMetrics(
        tenant_id=request.tenant_id,
        ticket_id=request.ticket_id,
        reply_count=request.reply_count,
        reopen_count=request.reopen_count,
        updated_by=created_by,
    )
    db.add(metrics)
    commit_or_raise(db, refresh=metrics, action="create ticket metrics")
    snapshot = _snapshot(metrics)
    TicketMetricsProducer.send_ticket_metrics_created(
        tenant_id=request.tenant_id, payload=snapshot
    )
    return metrics


def get_ticket_metrics(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    metrics_id: uuid.UUID,
) -> TicketMetrics:
    """Retrieve a ticket metrics record by ID within a tenant context."""
    metrics = (
        db.query(TicketMetrics)
        .filter(
            TicketMetrics.id == metrics_id,
            TicketMetrics.tenant_id == tenant_id,
        )
        .first()
    )
    if not metrics:
        logger.info(
            "Ticket metrics not found: tenant_id=%s, id=%s", tenant_id, metrics_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket metrics not found")
    return metrics


def update_ticket_metrics(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    metrics_id: uuid.UUID,
    request: TicketMetricsUpdate,
    updated_by: str,
) -> TicketMetrics:
    """Update an existing ticket metrics record and publish an updated event."""
    metrics = get_ticket_metrics(db, tenant_id=tenant_id, metrics_id=metrics_id)
    updates: Dict[str, Any] = {}
    if request.reply_count is not None:
        updates["reply_count"] = request.reply_count
    if request.reopen_count is not None:
        updates["reopen_count"] = request.reopen_count
    if not updates:
        return metrics  # nothing to update
    delta = _compute_delta(metrics, updates)
    for field, value in updates.items():
        setattr(metrics, field, value)
    metrics.updated_by = updated_by
    metrics.updated_at = datetime.utcnow()
    commit_or_raise(db, refresh=metrics, action="update ticket metrics")
    snapshot = _snapshot(metrics)
    TicketMetricsProducer.send_ticket_metrics_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=snapshot,
    )
    return metrics


def delete_ticket_metrics(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    metrics_id: uuid.UUID,
) -> None:
    """Delete a metrics record and publish a deleted event."""
    metrics = get_ticket_metrics(db, tenant_id=tenant_id, metrics_id=metrics_id)
    db.delete(metrics)
    commit_or_raise(db, action="delete ticket metrics")
    # Provide deletion timestamp in ISO format
    deleted_dt = datetime.utcnow().isoformat()
    TicketMetricsProducer.send_ticket_metrics_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None