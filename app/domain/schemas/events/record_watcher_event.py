"""
Event message schemas for record watcher lifecycle events.

These Pydantic models define the payloads for record watcher events.  When a
watcher is created or deleted, an event is emitted via the messaging
infrastructure to notify downstream consumers.  The messages follow the
same conventions as other entity events in the CRM service: a base
message carrying the tenant identifier and specific messages for
created and deleted lifecycle events.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class RecordWatcherBaseMessage(BaseModel):
    """Base fields common to all record watcher events."""

    tenant_id: UUID


class RecordWatcherCreatedMessage(RecordWatcherBaseMessage):
    """Event emitted when a record watcher is created."""

    payload: Dict[str, Any]


class RecordWatcherDeletedMessage(RecordWatcherBaseMessage):
    """Event emitted when a record watcher is deleted."""

    deleted_dt: Optional[str] = None