"""
Event models for TicketStatusDuration lifecycle.

This module defines payload schemas for events emitted when ticket
status duration records are created, updated, or deleted.  Each event
includes the tenant identifier, a delta describing changes, and the
full record after the operation.  The ``payload`` key holds the full
record for downstream processing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketStatusDurationDelta(BaseModel):
    """Represents changes to base fields for a status duration record."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketStatusDurationCreatedEvent(BaseModel):
    """Payload for a ticket_status_duration.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full status duration snapshot after creation"
    )


class TicketStatusDurationUpdatedEvent(BaseModel):
    """Payload for a ticket_status_duration.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketStatusDurationDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full status duration snapshot after update"
    )


class TicketStatusDurationDeletedEvent(BaseModel):
    """Payload for a ticket_status_duration.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp when the status duration was deleted",
    )


__all__ = [
    "TicketStatusDurationDelta",
    "TicketStatusDurationCreatedEvent",
    "TicketStatusDurationUpdatedEvent",
    "TicketStatusDurationDeletedEvent",
]