"""
Event models for TicketAiWorkRef lifecycle.

These classes define the payload structure for events emitted when
ticket AI work references are created, updated, or deleted. Each event
includes the tenant identifier and either a payload or delta describing
the state of the record.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketAiWorkRefDelta(BaseModel):
    """Delta describing changed fields on a ticket AI work reference."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None, description="Dictionary of changed fields on the AI work reference"
    )


class TicketAiWorkRefCreatedEvent(BaseModel):
    """Event published when a ticket AI work reference is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


class TicketAiWorkRefUpdatedEvent(BaseModel):
    """Event published when a ticket AI work reference is updated."""

    tenant_id: uuid.UUID
    delta: TicketAiWorkRefDelta
    payload: Dict[str, Any]


class TicketAiWorkRefDeletedEvent(BaseModel):
    """Event published when a ticket AI work reference is deleted."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


__all__ = [
    "TicketAiWorkRefDelta",
    "TicketAiWorkRefCreatedEvent",
    "TicketAiWorkRefUpdatedEvent",
    "TicketAiWorkRefDeletedEvent",
]