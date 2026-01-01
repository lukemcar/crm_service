"""
Event models for Knowledge Base Category lifecycle.

This module defines payload schemas for knowledge base category events
emitted via the messaging layer.  Each event corresponds to a CRUD
operation occurring on KbCategory entities.  A delta structure is
provided for update events to describe changes across base fields.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KbCategoryDelta(BaseModel):
    """Represents the set of changed base fields for a knowledge base category."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class KbCategoryCreatedEvent(BaseModel):
    """Payload for a kb_category.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base category snapshot after creation"
    )


class KbCategoryUpdatedEvent(BaseModel):
    """Payload for a kb_category.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: KbCategoryDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base category snapshot after update"
    )


class KbCategoryDeletedEvent(BaseModel):
    """Payload for a kb_category.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the category was deleted",
    )


__all__ = [
    "KbCategoryDelta",
    "KbCategoryCreatedEvent",
    "KbCategoryUpdatedEvent",
    "KbCategoryDeletedEvent",
]