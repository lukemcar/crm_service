"""Pydantic schemas for the TicketTimeEntry domain.

These models define the request and response structures used when
creating, updating, and retrieving time tracking entries on tickets.
Separate request models exist for tenant and admin contexts. Response
models mirror the ORM model and include audit metadata.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketTimeEntryBase(BaseModel):
    """Shared attributes for creating or updating a time entry."""

    minutes_spent: int = Field(
        ...,
        ge=0,
        description="Number of minutes spent on the ticket",
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Identifier of the user who logged the time (optional). If omitted, defaults to the authenticated user.",
    )
    work_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional categorization of the type of work performed",
    )
    note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional note about the work performed",
    )
    started_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the work started (ISO 8601 format)",
    )
    ended_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the work ended (ISO 8601 format)",
    )


class TenantCreateTicketTimeEntry(TicketTimeEntryBase):
    """Request model for creating a time entry in the tenant context.

    The ``ticket_id`` is provided via the path parameter and therefore
    omitted here. ``tenant_id`` is also provided via the path.
    """

    pass


class AdminCreateTicketTimeEntry(TicketTimeEntryBase):
    """Request model for creating a time entry via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the time entry will be created"
    )
    ticket_id: uuid.UUID = Field(
        ..., description="Ticket identifier for which the time entry will be created"
    )


class TicketTimeEntryUpdate(BaseModel):
    """Request model for updating a time entry.

    All fields are optional; only provided fields will be updated. ``minutes_spent``
    must remain non-negative if supplied. Updating ``user_id`` should be
    restricted to administrators via the admin API.
    """

    minutes_spent: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated number of minutes spent",
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Updated user identifier who logged the time (admin only)",
    )
    work_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Updated work type",
    )
    note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated note about the time entry",
    )
    started_at: Optional[str] = Field(
        default=None,
        description="Updated start time (ISO 8601) for the time entry",
    )
    ended_at: Optional[str] = Field(
        default=None,
        description="Updated end time (ISO 8601) for the time entry",
    )


class TicketTimeEntryOut(BaseModel):
    """Response model representing a time entry."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    minutes_spent: int
    work_type: Optional[str] = None
    note: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketTimeEntryBase",
    "TenantCreateTicketTimeEntry",
    "AdminCreateTicketTimeEntry",
    "TicketTimeEntryUpdate",
    "TicketTimeEntryOut",
]