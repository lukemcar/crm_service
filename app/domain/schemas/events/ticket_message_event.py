"""
Event models for TicketMessage lifecycle.

This module defines the payload structure for ticket message events
emitted via the messaging layer.  Messages are append‑only; only
creation events are defined.  Each event includes the tenant_id for
routing and filtering by downstream consumers.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketMessageDelta(BaseModel):
    """Delta describing changed fields on a ticket message (unused)."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of changed fields on the message",
    )


class TicketMessageCreatedEvent(BaseModel):
    """Event published when a ticket message is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


__all__ = [
    "TicketMessageDelta",
    "TicketMessageCreatedEvent",
]