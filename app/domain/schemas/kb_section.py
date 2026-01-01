"""
Pydantic schemas for Knowledge Base Section domain.

Sections group articles within categories.  These schemas define the
request and response models for creating, updating, and retrieving sections
through the API.  Creation schemas differ for tenant vs admin contexts to
ensure the tenant ID is supplied appropriately.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KbSectionBase(BaseModel):
    """Shared attributes for knowledge base sections."""

    kb_category_id: uuid.UUID = Field(
        ..., description="Identifier of the parent category"
    )
    name: str = Field(..., max_length=255, description="Section name")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional section description"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the section is active"
    )


class TenantCreateKbSection(KbSectionBase):
    """Request model for creating a section in tenant context."""

    pass


class AdminCreateKbSection(KbSectionBase):
    """Request model for creating a section via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the section")


class KbSectionUpdate(BaseModel):
    """Request model for updating an existing section."""

    name: Optional[str] = Field(default=None, max_length=255, description="Section name")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional section description"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether the section is active"
    )


class KbSectionOut(BaseModel):
    """Response model representing a knowledge base section."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    kb_category_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "KbSectionBase",
    "TenantCreateKbSection",
    "AdminCreateKbSection",
    "KbSectionUpdate",
    "KbSectionOut",
]