"""
Event models for SlaTarget lifecycle.

This module defines payload schemas for SLA target events emitted via
the messaging layer.  Each event corresponds to a CRUD operation on
SLA targets.  A delta structure is provided for update events to
describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SlaTargetDelta(BaseModel):
    """Represents the set of changed base fields for an SLA target."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class SlaTargetCreatedEvent(BaseModel):
    """Payload for a sla_target.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full SLA target snapshot after creation"
    )


class SlaTargetUpdatedEvent(BaseModel):
    """Payload for a sla_target.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: SlaTargetDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full SLA target snapshot after update"
    )


class SlaTargetDeletedEvent(BaseModel):
    """Payload for a sla_target.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the SLA target was deleted",
    )


__all__ = [
    "SlaTargetDelta",
    "SlaTargetCreatedEvent",
    "SlaTargetUpdatedEvent",
    "SlaTargetDeletedEvent",
]
