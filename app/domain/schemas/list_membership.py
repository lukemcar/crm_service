"""Pydantic schemas for ListMembership.

Defines structures for membership records in a list.  Usually
memberships are managed internally when lists are created or updated,
but these schemas can be used for administrative endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ListMembershipBase(BaseModel):
    list_id: UUID
    member_id: UUID
    member_type: str = Field(..., max_length=50)


class ListMembershipCreate(ListMembershipBase):
    pass


class ListMembershipRead(ListMembershipBase):
    id: UUID
    created_at: datetime
    created_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)