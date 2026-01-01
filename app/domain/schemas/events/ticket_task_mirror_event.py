"""
Event models for TicketTaskMirror lifecycle.

These classes define the payload structure for events emitted when
ticket task mirrors are created, updated, or deleted. Each event includes
the tenant identifier for routing and a payload or delta describing the
state of the record.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketTaskMirrorDelta(BaseModel):
    """Delta describing changed fields on a ticket task mirror."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None, description="Dictionary of changed fields on the task mirror"
    )


class TicketTaskMirrorCreatedEvent(BaseModel):
    """Event published when a ticket task mirror is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


class TicketTaskMirrorUpdatedEvent(BaseModel):
    """Event published when a ticket task mirror is updated."""

    tenant_id: uuid.UUID
    delta: TicketTaskMirrorDelta
    payload: Dict[str, Any]


class TicketTaskMirrorDeletedEvent(BaseModel):
    """Event published when a ticket task mirror is deleted."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


__all__ = [
    "TicketTaskMirrorDelta",
    "TicketTaskMirrorCreatedEvent",
    "TicketTaskMirrorUpdatedEvent",
    "TicketTaskMirrorDeletedEvent",
]