"""
Pydantic schemas for record watcher operations.

These models define the data structures used by the API and service
layer when creating or retrieving record watcher subscriptions.  A
watcher is identified by a tenant, record type and ID, and principal
type and ID.  The read schema exposes audit fields such as
``created_at`` and ``created_by_user_id``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecordWatcherBase(BaseModel):
    tenant_id: UUID
    record_type: str = Field(..., max_length=50)
    record_id: UUID
    principal_type: str = Field(..., max_length=20)
    principal_id: UUID


class RecordWatcherCreate(RecordWatcherBase):
    """Model for creating a new record watcher subscription."""

    # ``created_by_user_id`` is derived from the user header; omit from client
    pass


class RecordWatcherRead(RecordWatcherBase):
    """Model returned when reading an existing record watcher."""

    created_at: datetime
    created_by_user_id: Optional[UUID] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)


__all__ = ["RecordWatcherCreate", "RecordWatcherRead"]
