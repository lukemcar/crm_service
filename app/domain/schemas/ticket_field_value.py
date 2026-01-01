"""
Pydantic schemas for the TicketFieldValue domain.

These models define the request and response structures used when
creating, updating, and retrieving custom field values attached to
tickets.  Separate models exist for tenant and admin creation to
enforce explicit tenant scoping in the admin API.  Response models
include audit fields and mirror the ORM model.  Only the appropriate
value field should be supplied based on the associated field
definition's type.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class TicketFieldValueBase(BaseModel):
    """Shared attributes for creating or updating ticket field values."""

    ticket_field_def_id: uuid.UUID = Field(
        ..., description="Identifier of the custom field definition for which this value is provided"
    )
    # At most one of the following value fields should be populated
    value_text: Optional[str] = Field(
        default=None, description="Text value for the field (for text/textarea types)"
    )
    value_number: Optional[float] = Field(
        default=None, description="Numeric value for the field (for number types)"
    )
    value_bool: Optional[bool] = Field(
        default=None, description="Boolean value for the field (for boolean types)"
    )
    value_date: Optional[date] = Field(
        default=None, description="Date value for the field (for date types)"
    )
    value_ts: Optional[datetime] = Field(
        default=None, description="Timestamp value for the field (for datetime types)"
    )
    value_json: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON value for the field (for select/multiselect types)"
    )


class TenantCreateTicketFieldValue(TicketFieldValueBase):
    """Request model for creating a ticket field value in a tenant context."""
    # tenant_id and ticket_id provided via path
    pass


class AdminCreateTicketFieldValue(TicketFieldValueBase):
    """Request model for creating a ticket field value via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the field value will be created"
    )


class TicketFieldValueUpdate(BaseModel):
    """Request model for updating an existing ticket field value."""

    # At most one of these should be provided; others left as None
    value_text: Optional[str] = Field(
        default=None, description="Updated text value for the field"
    )
    value_number: Optional[float] = Field(
        default=None, description="Updated numeric value for the field"
    )
    value_bool: Optional[bool] = Field(
        default=None, description="Updated boolean value for the field"
    )
    value_date: Optional[date] = Field(
        default=None, description="Updated date value for the field"
    )
    value_ts: Optional[datetime] = Field(
        default=None, description="Updated timestamp value for the field"
    )
    value_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Updated JSON value for the field"
    )


class TicketFieldValueOut(BaseModel):
    """Response model representing a ticket field value."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    ticket_field_def_id: uuid.UUID
    value_text: Optional[str] = None
    value_number: Optional[float] = None
    value_bool: Optional[bool] = None
    value_date: Optional[date] = None
    value_ts: Optional[datetime] = None
    value_json: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketFieldValueBase",
    "TenantCreateTicketFieldValue",
    "AdminCreateTicketFieldValue",
    "TicketFieldValueUpdate",
    "TicketFieldValueOut",
]