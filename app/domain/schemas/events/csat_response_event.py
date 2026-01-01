"""Event models for CSAT response lifecycle.

Defines payload schemas for events emitted when CSAT responses are
created, updated, or deleted. Each event includes the tenant
identifier and relevant payload or delta information. Update and
delete events are reserved for administrative corrections.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CsatResponseDelta(BaseModel):
    """Represents the set of changed base fields for a CSAT response."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class CsatResponseCreatedEvent(BaseModel):
    """Payload for a csat_response.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full CSAT response snapshot after creation"
    )


class CsatResponseUpdatedEvent(BaseModel):
    """Payload for a csat_response.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: CsatResponseDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full CSAT response snapshot after update"
    )


class CsatResponseDeletedEvent(BaseModel):
    """Payload for a csat_response.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the CSAT response was deleted",
    )


__all__ = [
    "CsatResponseDelta",
    "CsatResponseCreatedEvent",
    "CsatResponseUpdatedEvent",
    "CsatResponseDeletedEvent",
]