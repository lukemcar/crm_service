"""
Service layer for SlaTarget entities.

This module provides CRUD operations for SLA targets, ensuring tenant
scoping and emitting domain events upon successful mutations.  Listing
operations support optional filtering by SLA policy and priority.
Unique constraints and check constraints are enforced at the database
layer; violations will surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.sla_target import SlaTarget
from app.domain.schemas.sla_target import (
    SlaTargetUpdate,
    TenantCreateSlaTarget,
    AdminCreateSlaTarget,
)
from app.domain.schemas.events.sla_target_event import SlaTargetDelta
from app.messaging.producers.sla_target_producer import (
    SlaTargetMessageProducer as SlaTargetProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("sla_target_service")


def _snapshot(target: SlaTarget) -> Dict[str, Any]:
    """Return a dictionary representation of a SlaTarget suitable for event payloads."""
    return {
        "id": target.id,
        "tenant_id": target.tenant_id,
        "sla_policy_id": target.sla_policy_id,
        "priority": target.priority,
        "first_response_minutes": target.first_response_minutes,
        "next_response_minutes": target.next_response_minutes,
        "resolution_minutes": target.resolution_minutes,
        "created_at": target.created_at.isoformat() if target.created_at else None,
        "created_by": target.created_by,
    }


def _compute_delta(target: SlaTarget, updates: Dict[str, Any]) -> SlaTargetDelta:
    """Compute a delta object for modified base fields on an SLA target."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        # Skip None values; only record actual changes
        if value is None:
            continue
        current = getattr(target, field)
        if current != value:
            changed[field] = value
    return SlaTargetDelta(base_fields=changed or None)


def list_sla_targets(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    sla_policy_id: Optional[uuid.UUID] = None,
    priority: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[SlaTarget], int]:
    """List SLA targets with optional filtering by policy and priority.

    If ``tenant_id`` is provided, results are scoped to that tenant.  If
    ``sla_policy_id`` is provided, results are limited to targets under
    that policy.  ``priority`` filters targets by priority value.  Results
    are ordered by creation time descending and can be paginated via
    ``limit`` and ``offset``.  Returns the list of targets and the
    total count.
    """
    logger.debug(
        "Listing SLA targets: tenant_id=%s, sla_policy_id=%s, priority=%s, limit=%s, offset=%s",
        tenant_id,
        sla_policy_id,
        priority,
        limit,
        offset,
    )
    query = db.query(SlaTarget)
    if tenant_id:
        query = query.filter(SlaTarget.tenant_id == tenant_id)
    if sla_policy_id:
        query = query.filter(SlaTarget.sla_policy_id == sla_policy_id)
    if priority:
        query = query.filter(SlaTarget.priority == priority)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(SlaTarget.created_at.desc())
    return query.all(), total


def create_sla_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateSlaTarget | AdminCreateSlaTarget,
    created_by: str,
) -> SlaTarget:
    """Create a new SLA target and publish a created event."""
    logger.debug(
        "Creating SLA target: tenant_id=%s, sla_policy_id=%s, priority=%s",
        tenant_id,
        request.sla_policy_id,
        request.priority,
    )
    target = SlaTarget(
        tenant_id=tenant_id,
        sla_policy_id=request.sla_policy_id,
        priority=request.priority,
        first_response_minutes=request.first_response_minutes,
        next_response_minutes=request.next_response_minutes,
        resolution_minutes=request.resolution_minutes,
        created_by=created_by,
    )
    db.add(target)
    commit_or_raise(db, refresh=target, action="create SLA target")
    snapshot = _snapshot(target)
    SlaTargetProducer.send_sla_target_created(tenant_id=tenant_id, payload=snapshot)
    return target


def get_sla_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    target_id: uuid.UUID,
) -> SlaTarget:
    """Retrieve an SLA target by ID within a tenant context."""
    target = (
        db.query(SlaTarget)
        .filter(
            SlaTarget.id == target_id,
            SlaTarget.tenant_id == tenant_id,
        )
        .first()
    )
    if not target:
        logger.info(
            "SLA target not found: tenant_id=%s, target_id=%s", tenant_id, target_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA target not found")
    return target


def update_sla_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    target_id: uuid.UUID,
    request: SlaTargetUpdate,
    updated_by: str,
) -> SlaTarget:
    """Update an existing SLA target and publish an update event."""
    target = get_sla_target(db, tenant_id=tenant_id, target_id=target_id)
    updates: Dict[str, Any] = {}
    for field in [
        "sla_policy_id",
        "priority",
        "first_response_minutes",
        "next_response_minutes",
        "resolution_minutes",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(target, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(target, field, value)
        # No updated_at column on SlaTarget; we record updated_by in created_by?? Not needed.
        commit_or_raise(db, refresh=target, action="update SLA target")
        snapshot = _snapshot(target)
        SlaTargetProducer.send_sla_target_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return target


def delete_sla_target(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    target_id: uuid.UUID,
) -> None:
    """Delete an SLA target and publish a deletion event."""
    target = get_sla_target(db, tenant_id=tenant_id, target_id=target_id)
    db.delete(target)
    commit_or_raise(db, action="delete SLA target")
    deleted_dt = datetime.utcnow().isoformat()
    SlaTargetProducer.send_sla_target_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_sla_targets",
    "create_sla_target",
    "get_sla_target",
    "update_sla_target",
    "delete_sla_target",
]
