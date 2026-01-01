"""
Pydantic schemas for the TicketForm domain.

These models define the request and response structures used when
creating, updating and retrieving custom ticket forms.  Separate
models exist for tenant and admin contexts to ensure that the
admin API explicitly specifies the tenant when creating forms.
Response models include audit fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketFormBase(BaseModel):
    """Shared attributes for ticket form creation and update."""

    name: str = Field(
        ..., max_length=255, description="Name of the form displayed to agents"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description of the form's purpose",
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Whether this form is available for selection when creating tickets",
    )


class TenantCreateTicketForm(TicketFormBase):
    """Request model for creating a ticket form in a tenant context."""
    # All fields are inherited from TicketFormBase.  tenant_id is provided as a path
    # parameter on the endpoint and therefore omitted here.
    pass


class AdminCreateTicketForm(TicketFormBase):
    """Request model for creating a ticket form via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the form will be created"
    )


class TicketFormUpdate(BaseModel):
    """Request model for updating an existing ticket form."""

    name: Optional[str] = Field(
        default=None, max_length=255, description="New name for the ticket form"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="New description of the ticket form",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the form should be active or inactive",
    )


class TicketFormOut(BaseModel):
    """Response model representing a ticket form."""

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
    "TicketFormBase",
    "TenantCreateTicketForm",
    "AdminCreateTicketForm",
    "TicketFormUpdate",
    "TicketFormOut",
]