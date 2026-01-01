"""
Event models for TicketMetrics lifecycle.

This module defines payload schemas for events emitted when ticket
metrics records are created, updated, or deleted.  Each event
carries a tenant identifier and either a full snapshot or a delta of
changed fields.  The ``payload`` key always contains the full
record after the operation for downstream consumers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketMetricsDelta(BaseModel):
    """Represents the set of changed base fields for a metrics record."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class TicketMetricsCreatedEvent(BaseModel):
    """Payload for a ticket_metrics.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full metrics snapshot after creation"
    )


class TicketMetricsUpdatedEvent(BaseModel):
    """Payload for a ticket_metrics.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: TicketMetricsDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full metrics snapshot after update"
    )


class TicketMetricsDeletedEvent(BaseModel):
    """Payload for a ticket_metrics.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the metrics record was deleted",
    )


__all__ = [
    "TicketMetricsDelta",
    "TicketMetricsCreatedEvent",
    "TicketMetricsUpdatedEvent",
    "TicketMetricsDeletedEvent",
]