"""
Event schemas for AutomationAction lifecycle.

This module defines payload structures for events emitted when
automation actions are created, updated or deleted.  Each event
includes the tenant context and either a full snapshot of the
automation action or a delta describing changed base fields.  The
structures mirror patterns used by other domain events such as
support macros【480489992503603†L264-L275】.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AutomationActionDelta(BaseModel):
    """Represents the set of changed base fields for an automation action."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None, description="Mapping of modified field names to their new values"
    )


class AutomationActionCreatedEvent(BaseModel):
    """Payload for an automation_action.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(..., description="Full automation action snapshot")


class AutomationActionUpdatedEvent(BaseModel):
    """Payload for an automation_action.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: AutomationActionDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full automation action snapshot after update"
    )


class AutomationActionDeletedEvent(BaseModel):
    """Payload for an automation_action.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None, description="ISO timestamp of when the action was deleted"
    )


__all__ = [
    "AutomationActionDelta",
    "AutomationActionCreatedEvent",
    "AutomationActionUpdatedEvent",
    "AutomationActionDeletedEvent",
]