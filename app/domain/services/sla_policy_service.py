"""
Service layer for SlaPolicy entities.

This module provides CRUD operations for SLA policies, ensuring tenant
scoping and emitting domain events upon successful mutations.  Listing
operations support optional filtering by active status.  Unique
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

from app.domain.models.sla_policy import SlaPolicy
from app.domain.schemas.sla_policy import (
    SlaPolicyUpdate,
    TenantCreateSlaPolicy,
    AdminCreateSlaPolicy,
)
from app.domain.schemas.events.sla_policy_event import SlaPolicyDelta
from app.messaging.producers.sla_policy_producer import (
    SlaPolicyMessageProducer as SlaPolicyProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("sla_policy_service")


def _snapshot(policy: SlaPolicy) -> Dict[str, Any]:
    """Return a dictionary representation of a SlaPolicy suitable for event payloads."""
    return {
        "id": policy.id,
        "tenant_id": policy.tenant_id,
        "name": policy.name,
        "description": policy.description,
        "is_active": policy.is_active,
        "match_rules": policy.match_rules,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        "created_by": policy.created_by,
        "updated_by": policy.updated_by,
    }


def _compute_delta(policy: SlaPolicy, updates: Dict[str, Any]) -> SlaPolicyDelta:
    """Compute a delta object for modified base fields on an SLA policy."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        # Skip None values; only record actual changes
        if value is None:
            continue
        current = getattr(policy, field)
        if current != value:
            changed[field] = value
    return SlaPolicyDelta(base_fields=changed or None)


def list_sla_policies(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[SlaPolicy], int]:
    """List SLA policies with optional filtering by active status and tenant.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``is_active`` filters policies by activation status.  Results are ordered by
    creation time descending and can be paginated via ``limit`` and
    ``offset``.  Returns the list of policies and the total count.
    """
    logger.debug(
        "Listing SLA policies: tenant_id=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        is_active,
        limit,
        offset,
    )
    query = db.query(SlaPolicy)
    if tenant_id:
        query = query.filter(SlaPolicy.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(SlaPolicy.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(SlaPolicy.created_at.desc())
    return query.all(), total


def create_sla_policy(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateSlaPolicy | AdminCreateSlaPolicy,
    created_by: str,
) -> SlaPolicy:
    """Create a new SLA policy and publish a created event."""
    logger.debug(
        "Creating SLA policy: tenant_id=%s, name=%s",
        tenant_id,
        request.name,
    )
    is_active = request.is_active if request.is_active is not None else True
    policy = SlaPolicy(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        is_active=is_active,
        match_rules=request.match_rules,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(policy)
    commit_or_raise(db, refresh=policy, action="create SLA policy")
    snapshot = _snapshot(policy)
    SlaPolicyProducer.send_sla_policy_created(tenant_id=tenant_id, payload=snapshot)
    return policy


def get_sla_policy(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    policy_id: uuid.UUID,
) -> SlaPolicy:
    """Retrieve an SLA policy by ID within a tenant context."""
    policy = (
        db.query(SlaPolicy)
        .filter(
            SlaPolicy.id == policy_id,
            SlaPolicy.tenant_id == tenant_id,
        )
        .first()
    )
    if not policy:
        logger.info(
            "SLA policy not found: tenant_id=%s, policy_id=%s", tenant_id, policy_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA policy not found")
    return policy


def update_sla_policy(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    policy_id: uuid.UUID,
    request: SlaPolicyUpdate,
    updated_by: str,
) -> SlaPolicy:
    """Update an existing SLA policy and publish an update event."""
    policy = get_sla_policy(db, tenant_id=tenant_id, policy_id=policy_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "description", "is_active", "match_rules"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(policy, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(policy, field, value)
        policy.updated_by = updated_by
        policy.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=policy, action="update SLA policy")
        snapshot = _snapshot(policy)
        SlaPolicyProducer.send_sla_policy_updated(
            tenant_id=tenant_id,
            changes=delta,
            payload=snapshot,
        )
    return policy


def delete_sla_policy(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    policy_id: uuid.UUID,
) -> None:
    """Delete an SLA policy and publish a deletion event."""
    policy = get_sla_policy(db, tenant_id=tenant_id, policy_id=policy_id)
    db.delete(policy)
    commit_or_raise(db, action="delete SLA policy")
    deleted_dt = datetime.utcnow().isoformat()
    SlaPolicyProducer.send_sla_policy_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_sla_policies",
    "create_sla_policy",
    "get_sla_policy",
    "update_sla_policy",
    "delete_sla_policy",
]
