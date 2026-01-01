"""
Event models for TicketTag lifecycle events.

These classes define the payload structure for events emitted when
ticket tags are created or deleted.  Tags are append-only, so only
creation and deletion events are defined.  Each event includes the
tenant_id for routing and filtering by downstream consumers.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketTagDelta(BaseModel):
    """Delta describing changed fields on a ticket tag (unused currently)."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of changed fields on the tag",
    )


class TicketTagCreatedEvent(BaseModel):
    """Event published when a ticket tag is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


class TicketTagDeletedEvent(BaseModel):
    """Event published when a ticket tag is deleted."""

    tenant_id: uuid.UUID
    deleted_dt: Optional[str] = Field(
        default=None, description="Timestamp when the deletion occurred"
    )


__all__ = [
    "TicketTagDelta",
    "TicketTagCreatedEvent",
    "TicketTagDeletedEvent",
]