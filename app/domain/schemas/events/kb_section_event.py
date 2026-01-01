"""
Event models for Knowledge Base Section lifecycle.

Defines payload schemas for knowledge base section events emitted via the
messaging layer.  Each event corresponds to a CRUD operation on KbSection
entities.  A delta structure describes modifications for update events.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KbSectionDelta(BaseModel):
    """Represents the set of changed base fields for a knowledge base section."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class KbSectionCreatedEvent(BaseModel):
    """Payload for a kb_section.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base section snapshot after creation"
    )


class KbSectionUpdatedEvent(BaseModel):
    """Payload for a kb_section.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: KbSectionDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base section snapshot after update"
    )


class KbSectionDeletedEvent(BaseModel):
    """Payload for a kb_section.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the section was deleted",
    )


__all__ = [
    "KbSectionDelta",
    "KbSectionCreatedEvent",
    "KbSectionUpdatedEvent",
    "KbSectionDeletedEvent",
]