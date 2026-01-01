"""
Event models for TicketForm lifecycle.

This module defines payload schemas for ticket form events emitted via
the messaging layer.  Each event corresponds to a CRUD operation
occurring on TicketForm entities.  A simple delta structure is
provided for update events to describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketFormDelta(BaseModel):
    """Represents the set of changed base fields for a ticket form."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketFormCreatedEvent(BaseModel):
    """Payload for a ticket_form.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket form snapshot after creation"
    )


class TicketFormUpdatedEvent(BaseModel):
    """Payload for a ticket_form.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketFormDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket form snapshot after update"
    )


class TicketFormDeletedEvent(BaseModel):
    """Payload for a ticket_form.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the ticket form was deleted",
    )


__all__ = [
    "TicketFormDelta",
    "TicketFormCreatedEvent",
    "TicketFormUpdatedEvent",
    "TicketFormDeletedEvent",
]