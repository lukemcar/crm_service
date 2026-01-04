"""
Event schemas for automation action lifecycle events.

These Pydantic models define the payloads for events emitted when an
automation action is created, updated or deleted.  Consumers can
subscribe to these events to trigger side effects in other systems.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class AutomationActionBaseEvent(BaseModel):
    """Common fields for all automation action events."""

    tenant_id: UUID


class AutomationActionCreatedEvent(AutomationActionBaseEvent):
    """Event emitted when an automation action is created."""

    payload: Dict[str, Any]


class AutomationActionUpdatedEvent(AutomationActionBaseEvent):
    """Event emitted when an automation action is updated."""

    payload: Dict[str, Any]


class AutomationActionDeletedEvent(AutomationActionBaseEvent):
    """Event emitted when an automation action is deleted."""

    deleted_dt: Optional[str] = None


__all__ = [
    "AutomationActionCreatedEvent",
    "AutomationActionUpdatedEvent",
    "AutomationActionDeletedEvent",
]