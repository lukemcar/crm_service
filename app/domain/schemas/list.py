"""Pydantic schemas for List (Segment).

Lists represent saved segments of records with a defined object type
and type (static or snapshot).  These schemas provide create, update and
read structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ListBase(BaseModel):
    name: str = Field(..., max_length=255)
    object_type: str = Field(..., max_length=50)
    list_type: str = Field(..., max_length=50)
    filter_definition: Optional[Any] = None

    # New optional fields for processing behaviour and archival status.  When
    # omitted on creation, defaults will be applied in the service layer.
    processing_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Processing behaviour for the list (e.g. STATIC)",
    )
    is_archived: Optional[bool] = Field(
        None,
        description="Whether the list is archived",
    )


class ListCreate(ListBase):
    """Schema for creating a list.

    All fields from :class:`ListBase` are accepted.  If ``processing_type`` or
    ``is_archived`` are omitted, defaults will be applied by the service
    layer.
    """
    pass


class ListUpdate(BaseModel):
    """Schema for updating a list.

    Only fields provided will be updated.  Fields omitted remain unchanged.
    """

    name: Optional[str] = Field(None, max_length=255)
    object_type: Optional[str] = Field(None, max_length=50)
    list_type: Optional[str] = Field(None, max_length=50)
    filter_definition: Optional[Any] = None

    # Optional updates for new fields
    processing_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Processing behaviour for the list (e.g. STATIC)",
    )
    is_archived: Optional[bool] = Field(
        None,
        description="Whether the list is archived",
    )


class ListRead(ListBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)