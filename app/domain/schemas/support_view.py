"""
Pydantic schemas for the SupportView domain.

These schemas define the request and response models used by the
support view API endpoints.  A support view stores a set of filters
and sort definitions for ticket lists.  Separate schemas exist for
tenant and admin creation to ensure the correct tenant context is
provided.  Update schemas allow partial modifications.  Response
models include audit fields and mirror the ORM model closely.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class SupportViewBase(BaseModel):
    """Shared attributes for support view creation and update."""

    name: str = Field(..., max_length=255, description="Name of the saved view")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional description of the view"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the view is active and visible"
    )
    filter_definition: Dict[str, Any] = Field(
        ..., description="JSON object encoding filter criteria for the view"
    )
    sort_definition: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional JSON object encoding sort preferences"
    )


class TenantCreateSupportView(SupportViewBase):
    """Request model for creating a support view in a tenant context."""

    pass


class AdminCreateSupportView(SupportViewBase):
    """Request model for creating a support view via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the support view")


class SupportViewUpdate(BaseModel):
    """Request model for updating an existing support view."""

    name: Optional[str] = Field(default=None, max_length=255, description="Name of the saved view")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional description of the view"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether the view is active and visible"
    )
    filter_definition: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON object encoding filter criteria for the view"
    )
    sort_definition: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional JSON object encoding sort preferences"
    )


class SupportViewOut(BaseModel):
    """Response model representing a support view."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    filter_definition: Dict[str, Any]
    sort_definition: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None  # ISO timestamp string
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "SupportViewBase",
    "TenantCreateSupportView",
    "AdminCreateSupportView",
    "SupportViewUpdate",
    "SupportViewOut",
]