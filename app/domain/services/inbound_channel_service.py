"""
Service layer for InboundChannel entities.

This module provides CRUD operations for inbound channels, ensuring
tenant scoping and emitting domain events upon successful mutations.
Listing operations support optional filters for channel_type and
activation status.  Unique constraints and check constraints are
enforced at the database layer; violations will surface as
integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.inbound_channel import InboundChannel
from app.domain.schemas.inbound_channel import (
    TenantCreateInboundChannel,
    AdminCreateInboundChannel,
    InboundChannelUpdate,
)
from app.domain.schemas.events.inbound_channel_event import InboundChannelDelta
from app.messaging.producers.inbound_channel_producer import (
    InboundChannelMessageProducer as InboundChannelProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("inbound_channel_service")


def _snapshot(channel: InboundChannel) -> Dict[str, Any]:
    """Return a dictionary representation of an InboundChannel suitable for event payloads."""
    return {
        "id": channel.id,
        "tenant_id": channel.tenant_id,
        "channel_type": channel.channel_type,
        "name": channel.name,
        "external_ref": channel.external_ref,
        "config": channel.config,
        "is_active": channel.is_active,
        "created_at": channel.created_at.isoformat() if channel.created_at else None,
        "updated_at": channel.updated_at.isoformat() if channel.updated_at else None,
        "created_by": channel.created_by,
        "updated_by": channel.updated_by,
    }


def _compute_delta(channel: InboundChannel, updates: Dict[str, Any]) -> InboundChannelDelta:
    """Compute a delta object for modified base fields on an inbound channel."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(channel, field)
        # Use != for simple equality; JSON/Dict comparisons are fine here
        if current != value:
            changed[field] = value
    return InboundChannelDelta(base_fields=changed or None)


def list_inbound_channels(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    channel_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[InboundChannel], int]:
    """List inbound channels with optional filtering by type and status.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``channel_type`` filters on the exact channel_type value.  ``is_active``
    filters channels by activation status.  Results are ordered by
    creation time descending and can be paginated via ``limit`` and
    ``offset``.  Returns the list of channels and the total count.
    """
    logger.debug(
        "Listing inbound channels: tenant_id=%s, channel_type=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        channel_type,
        is_active,
        limit,
        offset,
    )
    query = db.query(InboundChannel)
    if tenant_id:
        query = query.filter(InboundChannel.tenant_id == tenant_id)
    if channel_type:
        query = query.filter(InboundChannel.channel_type == channel_type)
    if is_active is not None:
        query = query.filter(InboundChannel.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(InboundChannel.created_at.desc())
    return query.all(), total


def create_inbound_channel(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateInboundChannel | AdminCreateInboundChannel,
    created_by: str,
) -> InboundChannel:
    """Create a new inbound channel and publish a created event."""
    logger.debug(
        "Creating inbound channel: tenant_id=%s, channel_type=%s, name=%s",
        tenant_id,
        request.channel_type,
        request.name,
    )
    channel = InboundChannel(
        tenant_id=tenant_id,
        channel_type=request.channel_type,
        name=request.name,
        external_ref=request.external_ref,
        config=request.config,
        is_active=request.is_active if request.is_active is not None else True,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(channel)
    commit_or_raise(db, refresh=channel, action="create inbound channel")
    snapshot = _snapshot(channel)
    InboundChannelProducer.send_inbound_channel_created(tenant_id=tenant_id, payload=snapshot)
    return channel


def get_inbound_channel(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
) -> InboundChannel:
    """Retrieve an inbound channel by ID within a tenant context."""
    channel = (
        db.query(InboundChannel)
        .filter(
            InboundChannel.id == channel_id,
            InboundChannel.tenant_id == tenant_id,
        )
        .first()
    )
    if not channel:
        logger.info(
            "Inbound channel not found: tenant_id=%s, channel_id=%s", tenant_id, channel_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbound channel not found")
    return channel


def update_inbound_channel(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
    request: InboundChannelUpdate,
    updated_by: str,
) -> InboundChannel:
    """Update an existing inbound channel and publish an update event."""
    channel = get_inbound_channel(db, tenant_id=tenant_id, channel_id=channel_id)
    updates: Dict[str, Any] = {}
    for field in ["channel_type", "name", "external_ref", "config", "is_active"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(channel, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(channel, field, value)
        channel.updated_by = updated_by
        channel.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=channel, action="update inbound channel")
        snapshot = _snapshot(channel)
        InboundChannelProducer.send_inbound_channel_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return channel


def delete_inbound_channel(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
) -> None:
    """Delete an inbound channel and publish a deletion event."""
    channel = get_inbound_channel(db, tenant_id=tenant_id, channel_id=channel_id)
    db.delete(channel)
    commit_or_raise(db, action="delete inbound channel")
    deleted_dt = datetime.utcnow().isoformat()
    InboundChannelProducer.send_inbound_channel_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_inbound_channels",
    "create_inbound_channel",
    "get_inbound_channel",
    "update_inbound_channel",
    "delete_inbound_channel",
]