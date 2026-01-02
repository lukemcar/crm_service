"""
Admin FastAPI routes for inbound channels.

These endpoints allow administrators to list, create, update, retrieve
and delete inbound channels across tenants.  Listing supports
optional tenant scoping for cross‑tenant searches.  Create and
mutation operations require an explicit ``tenant_id`` in the request
body or query parameter to ensure that the operation applies within
the correct tenant.  Audit fields are populated from the
``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.inbound_channel_service import (
    list_inbound_channels as service_list_inbound_channels,
    create_inbound_channel as service_create_inbound_channel,
    update_inbound_channel as service_update_inbound_channel,
    get_inbound_channel as service_get_inbound_channel,
    delete_inbound_channel as service_delete_inbound_channel,
)
from app.domain.schemas.inbound_channel import (
    AdminCreateInboundChannel,
    InboundChannelUpdate,
    InboundChannelOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/inbound_channels",
    tags=["InboundChannels"],
)


@router.get("/", response_model=PaginationEnvelope[InboundChannelOut])
def list_inbound_channels_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    channel_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[InboundChannelOut]:
    """List or search inbound channels across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Filters perform exact matches on channel_type and is_active.  Results
    are ordered by creation date descending and wrapped in a pagination
    envelope.  The total matching count is included.
    """
    channels, total = service_list_inbound_channels(
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
def create_inbound_channel_admin(
    *,
    channel_in: AdminCreateInboundChannel,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> InboundChannelOut:
    """Create a new inbound channel on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateInboundChannel``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    channel = service_create_inbound_channel(
        db,
        tenant_id=channel_in.tenant_id,
        request=channel_in,
        created_by=created_user,
    )
    return InboundChannelOut.model_validate(channel, from_attributes=True)


@router.patch("/{channel_id}", response_model=InboundChannelOut)
def update_inbound_channel_admin(
    *,
    channel_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the inbound channel to update"
    ),
    channel_update: InboundChannelUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> InboundChannelOut:
    """Apply updates to an inbound channel as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    channel = service_update_inbound_channel(
        db,
        tenant_id=tenant_id,
        channel_id=channel_id,
        request=channel_update,
        updated_by=updated_user,
    )
    return InboundChannelOut.model_validate(channel, from_attributes=True)


@router.get("/{channel_id}", response_model=InboundChannelOut)
def get_inbound_channel_admin(
    *,
    channel_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the inbound channel to retrieve"
    ),
    db: Session = Depends(get_db),
) -> InboundChannelOut:
    """Retrieve an inbound channel across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    channel can be resolved in the correct tenant context.  Raises 404
    if the channel does not exist in the tenant.
    """
    channel = service_get_inbound_channel(
        db, tenant_id=tenant_id, channel_id=channel_id
    )
    return InboundChannelOut.model_validate(channel, from_attributes=True)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inbound_channel_admin(
    *,
    channel_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the inbound channel to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an inbound channel as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_inbound_channel(
        db, tenant_id=tenant_id, channel_id=channel_id
    )
    return None
