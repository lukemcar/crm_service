"""
Event models for InboundChannel lifecycle.

This module defines payload schemas for inbound channel events emitted
via the messaging layer.  Each event corresponds to a CRUD
operation occurring on InboundChannel entities.  Update events carry a
delta describing which base fields changed.  These models are
intentionally simple; consumers should not depend on the internal
structure of ``payload`` beyond what is documented in service code.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InboundChannelDelta(BaseModel):
    """Represents the set of changed base fields for an inbound channel."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class InboundChannelCreatedEvent(BaseModel):
    """Payload for an inbound_channel.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full inbound channel snapshot after creation"
    )


class InboundChannelUpdatedEvent(BaseModel):
    """Payload for an inbound_channel.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: InboundChannelDelta = Field(
        ..., description="Delta describing modifications to the channel"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full inbound channel snapshot after update"
    )


class InboundChannelDeletedEvent(BaseModel):
    """Payload for an inbound_channel.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None, description="ISO timestamp of when the channel was deleted"
    )


__all__ = [
    "InboundChannelDelta",
    "InboundChannelCreatedEvent",
    "InboundChannelUpdatedEvent",
    "InboundChannelDeletedEvent",
]