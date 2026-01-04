"""
Event schemas for record watcher lifecycle events.

When a principal subscribes to or unsubscribes from a record,
the service layer emits an event to notify other systems.  These
schemas define the payloads for created and deleted events.  No
update event is defined since watchers cannot be modified in
place—subscribers must unsubscribe and resubscribe if they wish to
change their record or principal.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class RecordWatcherBaseEvent(BaseModel):
    """Common fields for record watcher events."""

    tenant_id: UUID


class RecordWatcherCreatedEvent(RecordWatcherBaseEvent):
    """Event emitted when a record watcher is created."""

    payload: Dict[str, Any]


class RecordWatcherDeletedEvent(RecordWatcherBaseEvent):
    """Event emitted when a record watcher is deleted."""

    deleted_dt: Optional[str] = None


__all__ = [
    "RecordWatcherCreatedEvent",
    "RecordWatcherDeletedEvent",
]
