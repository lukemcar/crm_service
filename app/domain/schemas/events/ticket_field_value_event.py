"""
Event models for TicketFieldValue lifecycle.

This module defines payload schemas for ticket_field_value events
emitted via the messaging layer.  Each event corresponds to a CRUD
operation occurring on TicketFieldValue entities.  A simple delta
structure is provided for update events to describe changes across
base fields (value_* columns).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketFieldValueDelta(BaseModel):
    """Represents the set of changed base fields for a ticket field value."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketFieldValueCreatedEvent(BaseModel):
    """Payload for a ticket_field_value.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket field value snapshot after creation"
    )


class TicketFieldValueUpdatedEvent(BaseModel):
    """Payload for a ticket_field_value.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketFieldValueDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket field value snapshot after update"
    )


class TicketFieldValueDeletedEvent(BaseModel):
    """Payload for a ticket_field_value.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the ticket field value was deleted",
    )


__all__ = [
    "TicketFieldValueDelta",
    "TicketFieldValueCreatedEvent",
    "TicketFieldValueUpdatedEvent",
    "TicketFieldValueDeletedEvent",
]