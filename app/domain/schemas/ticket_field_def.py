"""
Pydantic schemas for the TicketFieldDef domain.

These models define the request and response structures used when
creating, updating and retrieving custom ticket field definitions.
Separate models exist for tenant and admin creation to enforce
explicit tenant scoping in the admin API.  Response models include
audit fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketFieldDefBase(BaseModel):
    """Shared attributes for ticket field definition creation and update."""

    field_key: str = Field(
        ..., max_length=100, description="Stable key for the custom field"
    )
    label: str = Field(
        ..., max_length=255, description="Human‑friendly label for the field"
    )
    field_type: str = Field(
        ...,
        description="Type of the field (text, textarea, number, boolean, date, datetime, select, multiselect)",
    )
    is_required: Optional[bool] = Field(
        default=False, description="Whether the field must be provided when part of a form"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the field definition is active"
    )
    validation: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional JSON schema or rules for validation"
    )
    ui_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional UI configuration for rendering this field"
    )


class TenantCreateTicketFieldDef(TicketFieldDefBase):
    """Request model for creating a ticket field definition in a tenant context."""
    # tenant_id provided as path parameter
    pass


class AdminCreateTicketFieldDef(TicketFieldDefBase):
    """Request model for creating a ticket field definition via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the field definition will be created"
    )


class TicketFieldDefUpdate(BaseModel):
    """Request model for updating an existing ticket field definition."""

    label: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New human‑friendly label for the field",
    )
    field_type: Optional[str] = Field(
        default=None,
        description="New type for the field (must be one of the allowed values)",
    )
    is_required: Optional[bool] = Field(
        default=None,
        description="Whether the field should be required",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the field definition should be active",
    )
    validation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated validation rules for the field",
    )
    ui_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated UI configuration for rendering this field",
    )


class TicketFieldDefOut(BaseModel):
    """Response model representing a ticket field definition."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    field_key: str
    label: str
    field_type: str
    is_required: bool
    is_active: bool
    validation: Optional[Dict[str, Any]] = None
    ui_config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketFieldDefBase",
    "TenantCreateTicketFieldDef",
    "AdminCreateTicketFieldDef",
    "TicketFieldDefUpdate",
    "TicketFieldDefOut",
]