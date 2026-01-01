"""
Event models for SupportMacro lifecycle.

This module defines payload schemas for support macro events emitted
via the messaging layer.  Each event corresponds to a CRUD operation
on SupportMacro entities.  A delta structure is provided for update
events to describe modifications to base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SupportMacroDelta(BaseModel):
    """Represents the set of changed base fields for a support macro."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class SupportMacroCreatedEvent(BaseModel):
    """Payload for a support_macro.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(..., description="Full support macro snapshot")


class SupportMacroUpdatedEvent(BaseModel):
    """Payload for a support_macro.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: SupportMacroDelta = Field(..., description="Delta describing modifications")
    payload: Dict[str, Any] = Field(..., description="Full support macro snapshot after update")


class SupportMacroDeletedEvent(BaseModel):
    """Payload for a support_macro.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None, description="ISO timestamp of when the macro was deleted"
    )


__all__ = [
    "SupportMacroDelta",
    "SupportMacroCreatedEvent",
    "SupportMacroUpdatedEvent",
    "SupportMacroDeletedEvent",
]