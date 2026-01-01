"""
Event models for GroupProfile lifecycle.

This module defines payload schemas for group profile events emitted via
the messaging layer.  Each event corresponds to a CRUD operation
occurring on GroupProfile entities.  A simple delta structure is
provided for update events to describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GroupProfileDelta(BaseModel):
    """Represents the set of changed base fields for a group profile."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class GroupProfileCreatedEvent(BaseModel):
    """Payload for a group profile created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(..., description="Full group profile snapshot")


class GroupProfileUpdatedEvent(BaseModel):
    """Payload for a group profile updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: GroupProfileDelta = Field(..., description="Delta describing modifications")
    payload: Dict[str, Any] = Field(..., description="Full group profile snapshot after update")


class GroupProfileDeletedEvent(BaseModel):
    """Payload for a group profile deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(None, description="ISO timestamp of when the profile was deleted")


__all__ = [
    "GroupProfileDelta",
    "GroupProfileCreatedEvent",
    "GroupProfileUpdatedEvent",
    "GroupProfileDeletedEvent",
]
