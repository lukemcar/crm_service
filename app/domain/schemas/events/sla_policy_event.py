"""
Event models for SlaPolicy lifecycle.

This module defines payload schemas for SLA policy events emitted via
the messaging layer.  Each event corresponds to a CRUD operation on
SLA policies.  A delta structure is provided for update events to
describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SlaPolicyDelta(BaseModel):
    """Represents the set of changed base fields for an SLA policy."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class SlaPolicyCreatedEvent(BaseModel):
    """Payload for a sla_policy.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full SLA policy snapshot after creation"
    )


class SlaPolicyUpdatedEvent(BaseModel):
    """Payload for a sla_policy.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: SlaPolicyDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full SLA policy snapshot after update"
    )


class SlaPolicyDeletedEvent(BaseModel):
    """Payload for a sla_policy.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the SLA policy was deleted",
    )


__all__ = [
    "SlaPolicyDelta",
    "SlaPolicyCreatedEvent",
    "SlaPolicyUpdatedEvent",
    "SlaPolicyDeletedEvent",
]
