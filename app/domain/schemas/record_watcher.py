"""
Pydantic schemas for RecordWatcher.

These schemas define the shape of data used to create and read record
watcher records.  A record watcher associates a principal (user or
group) with a CRM record so that changes to the record can be
observed or notified.  The create schema excludes tenant_id as this
is typically derived from the authenticated context or route path.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RecordWatcherBase(BaseModel):
    """Base fields common to record watcher operations."""

    record_type: str = Field(..., max_length=50, description="Type of the record being watched")
    record_id: UUID
    principal_type: str = Field(
        ..., max_length=50, description="Type of the principal subscribing to changes"
    )
    principal_id: UUID


class RecordWatcherCreate(RecordWatcherBase):
    """Schema for creating a record watcher."""

    pass


class RecordWatcherRead(RecordWatcherBase):
    """Schema for reading a record watcher."""

    tenant_id: UUID
    created_at: datetime
    created_by_user_id: Optional[str] = None

    # Configure Pydantic v2 to allow ORM loading
    model_config = ConfigDict(from_attributes=True)