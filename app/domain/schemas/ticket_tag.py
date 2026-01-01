"""
Pydantic schemas for TicketTag.

These models define the request and response structures for managing
tags on tickets.  Tags are simple strings attached to a ticket for
categorisation and filtering.  Separate request schemas exist for
tenant and admin contexts.  Response models include audit fields
mirroring the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketTagBase(BaseModel):
    """Shared attributes for creating a ticket tag."""

    tag: str = Field(..., max_length=100, description="Tag string to attach to the ticket")


class TenantCreateTicketTag(TicketTagBase):
    """Request model for creating a ticket tag in a tenant context."""

    pass


class AdminCreateTicketTag(TicketTagBase):
    """Request model for creating a ticket tag via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the ticket tag"
    )


class TicketTagOut(BaseModel):
    """Response model representing a ticket tag."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    tag: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketTagBase",
    "TenantCreateTicketTag",
    "AdminCreateTicketTag",
    "TicketTagOut",
]