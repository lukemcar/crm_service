"""
Pydantic schemas for Ticket SLA State domain.

These models define request and response structures for retrieving and
updating ticket SLA state.  SLA state records computed deadlines and
breach flags for tickets.  Tenant and admin users can read these
records; admin users may update them via an internal endpoint to
support orchestration backfills.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketSlaStateUpdate(BaseModel):
    """Request model for updating an existing ticket SLA state.

    This is primarily intended for admin/internal use, for example
    when orchestration recomputes SLA deadlines.  All fields are
    optional; fields omitted will not be modified.
    """

    sla_policy_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the applied SLA policy"
    )
    first_response_due_at: Optional[str] = Field(
        default=None, description="ISO timestamp when first response is due"
    )
    next_response_due_at: Optional[str] = Field(
        default=None, description="ISO timestamp when next response is due"
    )
    resolution_due_at: Optional[str] = Field(
        default=None, description="ISO timestamp when resolution is due"
    )
    first_response_breached: Optional[bool] = Field(
        default=None, description="Whether the first response deadline is breached"
    )
    next_response_breached: Optional[bool] = Field(
        default=None, description="Whether the next response deadline is breached"
    )
    resolution_breached: Optional[bool] = Field(
        default=None, description="Whether the resolution deadline is breached"
    )
    last_computed_at: Optional[str] = Field(
        default=None, description="ISO timestamp when the state was last computed"
    )


class TicketSlaStateOut(BaseModel):
    """Response model representing a ticket SLA state."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    sla_policy_id: Optional[uuid.UUID] = None
    first_response_due_at: Optional[str] = None
    next_response_due_at: Optional[str] = None
    resolution_due_at: Optional[str] = None
    first_response_breached: bool
    next_response_breached: bool
    resolution_breached: bool
    last_computed_at: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketSlaStateUpdate",
    "TicketSlaStateOut",
]
