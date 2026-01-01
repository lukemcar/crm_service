"""
Pydantic schemas for the SupportMacro domain.

Macros represent one‑click actions that agents can apply to tickets.  A
macro contains a name, optional description, activation flag and a
list of actions encoded as JSON.  Separate schemas exist for tenant
and admin creation to supply the tenant context when required.
Update schemas allow partial modification.  Response models include
audit fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SupportMacroBase(BaseModel):
    """Shared attributes for support macro creation and update."""

    name: str = Field(..., max_length=255, description="Name of the macro")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional description of the macro"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the macro is active and available"
    )
    actions: List[Dict[str, Any]] = Field(
        ..., description="List of operations comprising the macro"
    )


class TenantCreateSupportMacro(SupportMacroBase):
    """Request model for creating a support macro in a tenant context."""

    pass


class AdminCreateSupportMacro(SupportMacroBase):
    """Request model for creating a support macro via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the macro")


class SupportMacroUpdate(BaseModel):
    """Request model for updating an existing support macro."""

    name: Optional[str] = Field(default=None, max_length=255, description="Name of the macro")
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional description of the macro"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether the macro is active and available"
    )
    actions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of operations comprising the macro"
    )


class SupportMacroOut(BaseModel):
    """Response model representing a support macro."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    actions: List[Dict[str, Any]]
    created_at: Optional[str] = None  # ISO timestamp string
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "SupportMacroBase",
    "TenantCreateSupportMacro",
    "AdminCreateSupportMacro",
    "SupportMacroUpdate",
    "SupportMacroOut",
]