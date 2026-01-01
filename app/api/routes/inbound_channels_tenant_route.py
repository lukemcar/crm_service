"""
Tenant‑scoped FastAPI routes for inbound channels.

These endpoints allow tenants to list, create, update, retrieve and
delete inbound channels that belong to them.  Filters are provided
for channel type and active status.  Audit fields are populated
from the ``X-User`` header when provided; otherwise "anonymous" is
used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services import inbound_channel_service  # for mypy namespace support

from app.domain.schemas.inbound_channel import (
    TenantCreateInboundChannel,
    InboundChannelUpdate,
    InboundChannelOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/inbound_channels",
    tags=["InboundChannels"],
)


@router.get("/", response_model=PaginationEnvelope[InboundChannelOut])
def list_inbound_channels_endpoint(
    tenant_id: UUID,
    channel_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[InboundChannelOut]:
    """List inbound channels for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of channels.
    """
    channels, total = inbound_channel_service.list_inbound_channels(
        db,
        tenant_id=tenant_id,
        channel_type=channel_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items: List[InboundChannelOut] = [
        InboundChannelOut.model_validate(c, from_attributes=True) for c in channels
    ]
    return PaginationEnvelope[InboundChannelOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=InboundChannelOut, status_code=status.HTTP_201_CREATED)
def create_inbound_channel_endpoint(
    tenant_id: UUID,
    channel_in: TenantCreateInboundChannel,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> InboundChannelOut:
    """Create a new inbound channel for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the channel are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    channel = inbound_channel_service.create_inbound_channel(
        db,
        tenant_id=tenant_id,
        request=channel_in,
        created_by=created_user,
    )
    return InboundChannelOut.model_validate(channel, from_attributes=True)


@router.patch("/{channel_id}", response_model=InboundChannelOut)
def update_inbound_channel_endpoint(
    tenant_id: UUID,
    channel_id: UUID,
    channel_update: InboundChannelUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> InboundChannelOut:
    """Update an existing inbound channel.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    channel = inbound_channel_service.update_inbound_channel(
        db,
        tenant_id=tenant_id,
        channel_id=channel_id,
        request=channel_update,
        updated_by=updated_user,
    )
    return InboundChannelOut.model_validate(channel, from_attributes=True)


@router.get("/{channel_id}", response_model=InboundChannelOut)
def get_inbound_channel_endpoint(
    tenant_id: UUID,
    channel_id: UUID,
    db: Session = Depends(get_db),
) -> InboundChannelOut:
    """Retrieve a single inbound channel by ID within a tenant.

    Raises 404 if the channel does not exist or does not belong to
    the tenant.
    """
    channel = inbound_channel_service.get_inbound_channel(
        db, tenant_id=tenant_id, channel_id=channel_id
    )
    return InboundChannelOut.model_validate(channel, from_attributes=True)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inbound_channel_endpoint(
    tenant_id: UUID,
    channel_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete an inbound channel from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the channel does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events; event publishers
    do not include user information for deletions.
    """
    inbound_channel_service.delete_inbound_channel(
        db, tenant_id=tenant_id, channel_id=channel_id
    )
    return None
