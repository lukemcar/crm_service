"""
Pydantic schemas for the TicketFormField domain.

These models define the request and response structures used when
creating, updating, and retrieving associations between ticket
forms and custom field definitions.  Separate models exist for
tenant and admin creation to enforce explicit tenant scoping in the
admin API.  Response models include audit fields and mirror the
ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketFormFieldBase(BaseModel):
    """Shared attributes for creating or updating ticket form fields."""

    ticket_form_id: uuid.UUID = Field(
        ..., description="Identifier of the ticket form that this field belongs to"
    )
    ticket_field_def_id: uuid.UUID = Field(
        ..., description="Identifier of the custom field definition to include"
    )
    display_order: int = Field(
        ..., ge=0, description="Order in which the field should appear on the form"
    )


class TenantCreateTicketFormField(TicketFormFieldBase):
    """Request model for creating a ticket form field in a tenant context."""
    # tenant_id provided via path
    pass


class AdminCreateTicketFormField(TicketFormFieldBase):
    """Request model for creating a ticket form field via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the form field will be created"
    )


class TicketFormFieldUpdate(BaseModel):
    """Request model for updating an existing ticket form field."""

    display_order: Optional[int] = Field(
        default=None,
        ge=0,
        description="New display order for the field on the form"
    )


class TicketFormFieldOut(BaseModel):
    """Response model representing a ticket form field."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_form_id: uuid.UUID
    ticket_field_def_id: uuid.UUID
    display_order: int
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketFormFieldBase",
    "TenantCreateTicketFormField",
    "AdminCreateTicketFormField",
    "TicketFormFieldUpdate",
    "TicketFormFieldOut",
]