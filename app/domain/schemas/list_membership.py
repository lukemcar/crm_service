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
from enum import Enum


class ListObjectType(str, Enum):
    """Allowed CRM object types for list memberships.

    The change request introduced a dedicated ``list_object_type`` enum in the
    database.  This Python enum mirrors that type to provide type safety
    and validation at the API layer.  Additional values may be added as the
    CRM evolves.
    """

    contact = "contact"
    company = "company"
    deal = "deal"
    lead = "lead"


class ListMembershipBase(BaseModel):
    list_id: UUID
    member_id: UUID
    member_type: ListObjectType = Field(..., description="Type of the member record")


class ListMembershipCreate(ListMembershipBase):
    pass


class ListMembershipRead(ListMembershipBase):
    id: UUID
    created_at: datetime
    created_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)