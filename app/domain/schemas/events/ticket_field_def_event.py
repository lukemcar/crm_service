"""
Event models for TicketFieldDef lifecycle.

This module defines payload schemas for ticket field definition events
emitted via the messaging layer.  Each event corresponds to a CRUD
operation occurring on TicketFieldDef entities.  A delta structure is
provided for update events to describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketFieldDefDelta(BaseModel):
    """Represents the set of changed base fields for a ticket field definition."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketFieldDefCreatedEvent(BaseModel):
    """Payload for a ticket_field_def.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket field definition snapshot after creation"
    )


class TicketFieldDefUpdatedEvent(BaseModel):
    """Payload for a ticket_field_def.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketFieldDefDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket field definition snapshot after update"
    )


class TicketFieldDefDeletedEvent(BaseModel):
    """Payload for a ticket_field_def.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the ticket field definition was deleted",
    )


__all__ = [
    "TicketFieldDefDelta",
    "TicketFieldDefCreatedEvent",
    "TicketFieldDefUpdatedEvent",
    "TicketFieldDefDeletedEvent",
]