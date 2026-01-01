"""
Event models for TicketFormField lifecycle.

This module defines payload schemas for ticket_form_field events emitted
via the messaging layer.  Each event corresponds to a CRUD
operation occurring on TicketFormField entities.  A simple delta
structure is provided for update events to describe changes across
base fields (currently only ``display_order``).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketFormFieldDelta(BaseModel):
    """Represents the set of changed base fields for a ticket form field."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketFormFieldCreatedEvent(BaseModel):
    """Payload for a ticket_form_field.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket form field snapshot after creation"
    )


class TicketFormFieldUpdatedEvent(BaseModel):
    """Payload for a ticket_form_field.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketFormFieldDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket form field snapshot after update"
    )


class TicketFormFieldDeletedEvent(BaseModel):
    """Payload for a ticket_form_field.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the ticket form field was deleted",
    )


__all__ = [
    "TicketFormFieldDelta",
    "TicketFormFieldCreatedEvent",
    "TicketFormFieldUpdatedEvent",
    "TicketFormFieldDeletedEvent",
]