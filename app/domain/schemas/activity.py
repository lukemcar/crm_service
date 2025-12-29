"""Pydantic schemas for Activity.

Activities capture notes and tasks.  Notes only require a description,
while tasks include additional attributes like due date, status and
assigned user.  These schemas distinguish create, update and read
variants.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ActivityBase(BaseModel):
    type: str = Field(..., max_length=20)  # 'note' or 'task'
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)  # 'open', 'completed'
    assigned_user_id: Optional[UUID] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    assigned_user_id: Optional[UUID] = None


class ActivityRead(ActivityBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)