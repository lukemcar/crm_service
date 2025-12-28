"""Pydantic schemas for List (Segment).

Lists represent saved segments of records with a defined object type
and type (static or snapshot).  These schemas provide create, update and
read structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class ListBase(BaseModel):
    name: str = Field(..., max_length=255)
    object_type: str = Field(..., max_length=50)
    list_type: str = Field(..., max_length=50)
    filter_definition: Optional[Any] = None


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    object_type: Optional[str] = Field(None, max_length=50)
    list_type: Optional[str] = Field(None, max_length=50)
    filter_definition: Optional[Any] = None


class ListRead(ListBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        orm_mode = True