"""Pydantic schemas for ListMembership.

Defines structures for membership records in a list.  Usually
memberships are managed internally when lists are created or updated,
but these schemas can be used for administrative endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ListMembershipBase(BaseModel):
    list_id: UUID
    member_id: UUID
    member_type: str = Field(..., max_length=50)


class ListMembershipCreate(ListMembershipBase):
    pass


class ListMembershipRead(ListMembershipBase):
    id: UUID
    created_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        orm_mode = True