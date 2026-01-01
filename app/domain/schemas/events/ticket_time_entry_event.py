"""Event models for TicketTimeEntry lifecycle.

This module defines payload schemas for ticket time entry events. Each
event corresponds to a CRUD operation occurring on ``TicketTimeEntry``
entities. A simple delta structure is provided for update events to
describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketTimeEntryDelta(BaseModel):
    """Represents the set of changed base fields for a time entry."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketTimeEntryCreatedEvent(BaseModel):
    """Payload for a ticket_time_entry.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full time entry snapshot after creation"
    )


class TicketTimeEntryUpdatedEvent(BaseModel):
    """Payload for a ticket_time_entry.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketTimeEntryDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full time entry snapshot after update"
    )


class TicketTimeEntryDeletedEvent(BaseModel):
    """Payload for a ticket_time_entry.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the time entry was deleted",
    )


__all__ = [
    "TicketTimeEntryDelta",
    "TicketTimeEntryCreatedEvent",
    "TicketTimeEntryUpdatedEvent",
    "TicketTimeEntryDeletedEvent",
]