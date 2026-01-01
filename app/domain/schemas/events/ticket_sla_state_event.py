"""
Event models for TicketSlaState lifecycle.

This module defines payload schemas for ticket SLA state events emitted via
the messaging layer.  The primary event is ``ticket_sla_state.updated``
which captures changes in computed deadlines or breach flags for a
ticket's SLA state.  A delta structure is provided to describe
modified fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketSlaStateDelta(BaseModel):
    """Represents the set of changed fields for a ticket SLA state."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketSlaStateUpdatedEvent(BaseModel):
    """Payload for a ticket_sla_state.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    ticket_id: UUID = Field(..., description="Identifier of the ticket")
    changes: TicketSlaStateDelta = Field(
        ..., description="Delta describing modifications to state fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full ticket SLA state snapshot after update"
    )


__all__ = [
    "TicketSlaStateDelta",
    "TicketSlaStateUpdatedEvent",
]
