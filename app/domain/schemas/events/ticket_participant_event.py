"""
Event models for TicketParticipant lifecycle events.

These classes define the payload structure for events emitted when
ticket participants are created or deleted.  They are wrapped in an
EventEnvelope by the producer layer before being sent to the message
broker.  The ``base_fields`` in the delta may be used in the future
for update events; currently participants are append-only so only
creation and deletion events are defined.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketParticipantDelta(BaseModel):
    """Delta describing changed fields on a ticket participant (unused currently)."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of changed fields on the participant",
    )


class TicketParticipantCreatedEvent(BaseModel):
    """Event published when a ticket participant is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


class TicketParticipantDeletedEvent(BaseModel):
    """Event published when a ticket participant is deleted."""

    tenant_id: uuid.UUID
    deleted_dt: Optional[str] = Field(
        default=None, description="Timestamp when the deletion occurred"
    )


__all__ = [
    "TicketParticipantDelta",
    "TicketParticipantCreatedEvent",
    "TicketParticipantDeletedEvent",
]