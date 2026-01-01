"""
Pydantic schemas for Knowledge Base Category domain.

These schemas define the request and response models used by the
knowledge base category API endpoints.  Categories are the top-level
containers for sections and articles.  Creation and update schemas
validate input, and response schemas mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KbCategoryBase(BaseModel):
    """Shared attributes for knowledge base categories."""

    name: str = Field(..., max_length=255, description="Category name")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional category description"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the category is active"
    )


class TenantCreateKbCategory(KbCategoryBase):
    """Request model for creating a category in a tenant context."""

    pass


class AdminCreateKbCategory(KbCategoryBase):
    """Request model for creating a category via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the category")


class KbCategoryUpdate(BaseModel):
    """Request model for updating an existing category."""

    name: Optional[str] = Field(default=None, max_length=255, description="Category name")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional category description"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether the category is active"
    )


class KbCategoryOut(BaseModel):
    """Response model representing a category."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "KbCategoryBase",
    "TenantCreateKbCategory",
    "AdminCreateKbCategory",
    "KbCategoryUpdate",
    "KbCategoryOut",
]