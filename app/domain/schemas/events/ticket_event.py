"""
Event models for Ticket lifecycle.

This module defines payload schemas for ticket events emitted via the
messaging layer.  Each event corresponds to a CRUD operation
occurring on Ticket entities.  Update events carry a delta
describing which base fields changed.  These models should not be
coupled too tightly to downstream consumers; they exist to document
the shape of emitted events.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketDelta(BaseModel):
    """Represents the set of changed base fields for a ticket."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketCreatedEvent(BaseModel):
    """Payload for a ticket.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket snapshot after creation"
    )


class TicketUpdatedEvent(BaseModel):
    """Payload for a ticket.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketDelta = Field(
        ..., description="Delta describing modifications to the ticket"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket snapshot after update"
    )


class TicketDeletedEvent(BaseModel):
    """Payload for a ticket.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None, description="ISO timestamp of when the ticket was deleted"
    )


__all__ = [
    "TicketDelta",
    "TicketCreatedEvent",
    "TicketUpdatedEvent",
    "TicketDeletedEvent",
]