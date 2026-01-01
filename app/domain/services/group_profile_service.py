"""
Service layer for GroupProfile entities.

This module implements CRUD operations for the group profile domain.
Group profiles encapsulate support queue metadata such as default
SLA policies, routing configuration and AI posture.  The service
enforces tenant scoping, handles database transactions via
``commit_or_raise`` and emits events through the message producer
after successful mutations.  Listing operations support optional
filters on profile type and support queue status.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.group_profile import GroupProfile
from app.domain.schemas.group_profile import (
    TenantCreateGroupProfile,
    AdminCreateGroupProfile,
    GroupProfileUpdate,
)
from app.domain.schemas.events.group_profile_event import GroupProfileDelta
from app.messaging.producers.group_profile_producer import (
    GroupProfileMessageProducer as GroupProfileProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("group_profile_service")


def _snapshot(profile: GroupProfile) -> Dict[str, Any]:
    """Return a dictionary representation of a GroupProfile suitable for event payloads."""
    return {
        "id": profile.id,
        "tenant_id": profile.tenant_id,
        "group_id": profile.group_id,
        "profile_type": profile.profile_type,
        "is_support_queue": profile.is_support_queue,
        "is_assignable": profile.is_assignable,
        "default_sla_policy_id": profile.default_sla_policy_id,
        "routing_config": profile.routing_config,
        "ai_work_mode_default": profile.ai_work_mode_default,
        "business_hours_id": profile.business_hours_id,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        "created_by": profile.created_by,
        "updated_by": profile.updated_by,
    }


def _compute_delta(profile: GroupProfile, updates: Dict[str, Any]) -> GroupProfileDelta:
    """Compute the delta for updated base fields on a GroupProfile."""
    # Only include fields that actually changed
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        # Skip unchanged values or None
        if value is None:
            continue
        current = getattr(profile, field)
        if current != value:
            changed[field] = value
    return GroupProfileDelta(base_fields=changed or None)


def list_group_profiles(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    profile_type: Optional[str] = None,
    is_support_queue: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[GroupProfile], int]:
    """List group profiles with optional filters.

    If ``tenant_id`` is provided, results are scoped to that tenant.  The
    optional ``profile_type`` filter matches exactly on the profile_type
    column.  ``is_support_queue`` filters on the boolean flag.
    """
    logger.debug(
        "Listing group profiles: tenant_id=%s, profile_type=%s, is_support_queue=%s, limit=%s, offset=%s",
        tenant_id,
        profile_type,
        is_support_queue,
        limit,
        offset,
    )
    query = db.query(GroupProfile)
    if tenant_id:
        query = query.filter(GroupProfile.tenant_id == tenant_id)
    if profile_type:
        query = query.filter(GroupProfile.profile_type == profile_type)
    if is_support_queue is not None:
        query = query.filter(GroupProfile.is_support_queue == is_support_queue)

    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(GroupProfile.created_at.desc())
    return query.all(), total


def create_group_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateGroupProfile | AdminCreateGroupProfile,
    created_by: str,
) -> GroupProfile:
    """Create a group profile for a tenant and publish an event."""
    logger.debug(
        "Creating group profile: tenant_id=%s, group_id=%s", tenant_id, request.group_id
    )
    profile = GroupProfile(
        tenant_id=tenant_id,
        group_id=request.group_id,
        profile_type=request.profile_type or "support_queue",
        is_support_queue=request.is_support_queue if request.is_support_queue is not None else True,
        is_assignable=request.is_assignable if request.is_assignable is not None else True,
        default_sla_policy_id=request.default_sla_policy_id,
        routing_config=request.routing_config,
        ai_work_mode_default=request.ai_work_mode_default or "human_only",
        business_hours_id=request.business_hours_id,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(profile)
    commit_or_raise(db, refresh=profile, action="create group profile")

    # Emit event after commit
    snapshot = _snapshot(profile)
    GroupProfileProducer.send_group_profile_created(tenant_id=tenant_id, payload=snapshot)
    return profile


def get_group_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
) -> GroupProfile:
    """Retrieve a group profile by ID within a tenant."""
    profile = (
        db.query(GroupProfile)
        .filter(
            GroupProfile.id == profile_id,
            GroupProfile.tenant_id == tenant_id,
        )
        .first()
    )
    if not profile:
        logger.info(
            "Group profile not found: tenant_id=%s, profile_id=%s", tenant_id, profile_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group profile not found",
        )
    return profile


def update_group_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
    request: GroupProfileUpdate,
    updated_by: str,
) -> GroupProfile:
    """Update an existing group profile and publish a delta event."""
    profile = get_group_profile(db, tenant_id=tenant_id, profile_id=profile_id)
    updates: Dict[str, Any] = {}
    # Build updates dict; only consider fields present (not None)
    for field in [
        "profile_type",
        "is_support_queue",
        "is_assignable",
        "default_sla_policy_id",
        "routing_config",
        "ai_work_mode_default",
        "business_hours_id",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    # Compute delta relative to current state
    delta = _compute_delta(profile, updates)
    if delta.base_fields:
        # Apply changes
        for field, value in delta.base_fields.items():
            setattr(profile, field, value)
        profile.updated_by = updated_by
        profile.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=profile, action="update group profile")
        snapshot = _snapshot(profile)
        GroupProfileProducer.send_group_profile_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return profile


def delete_group_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
) -> None:
    """Delete a group profile and publish a deletion event."""
    profile = get_group_profile(db, tenant_id=tenant_id, profile_id=profile_id)
    db.delete(profile)
    commit_or_raise(db, action="delete group profile")
    # Emitting deleted event with timestamp
    deleted_dt = datetime.utcnow().isoformat()
    GroupProfileProducer.send_group_profile_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_group_profiles",
    "create_group_profile",
    "get_group_profile",
    "update_group_profile",
    "delete_group_profile",
]
