"""Pydantic schemas for Association.

Associations allow flexible linking between any two CRM records.  These
schemas describe the required fields for creating and reading
associations.  Updates are not typically supported as associations
should be immutable; clients can delete and recreate instead.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AssociationBase(BaseModel):
    from_object_type: str = Field(..., max_length=50)
    from_object_id: UUID
    to_object_type: str = Field(..., max_length=50)
    to_object_id: UUID
    association_type: Optional[str] = Field(None, max_length=50)


class AssociationCreate(AssociationBase):
    pass


class AssociationRead(AssociationBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    created_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)