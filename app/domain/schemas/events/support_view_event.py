"""
Event models for SupportView lifecycle.

This module defines payload schemas for support view events emitted via
the messaging layer.  Each event corresponds to a CRUD operation on
SupportView entities.  A delta structure is provided for update events
to describe modifications to base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SupportViewDelta(BaseModel):
    """Represents the set of changed base fields for a support view."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class SupportViewCreatedEvent(BaseModel):
    """Payload for a support_view.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(..., description="Full support view snapshot")


class SupportViewUpdatedEvent(BaseModel):
    """Payload for a support_view.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: SupportViewDelta = Field(..., description="Delta describing modifications")
    payload: Dict[str, Any] = Field(..., description="Full support view snapshot after update")


class SupportViewDeletedEvent(BaseModel):
    """Payload for a support_view.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None, description="ISO timestamp of when the view was deleted"
    )


__all__ = [
    "SupportViewDelta",
    "SupportViewCreatedEvent",
    "SupportViewUpdatedEvent",
    "SupportViewDeletedEvent",
]