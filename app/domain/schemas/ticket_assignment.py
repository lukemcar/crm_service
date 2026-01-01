"""
Pydantic schemas for TicketAssignment.

These models define request and response structures for managing
assignment history on tickets.  Assignments record which group or
agent a ticket has been assigned to, who performed the assignment,
an optional reason, and an AI session reference if applicable.
Assignments are append‑only.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketAssignmentBase(BaseModel):
    """Shared attributes for creating a ticket assignment."""

    assigned_group_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the group the ticket is assigned to"
    )
    assigned_user_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the user the ticket is assigned to"
    )
    assigned_by_user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Identifier of the user who performed the assignment",
    )
    assigned_by_reason: Optional[str] = Field(
        default=None, max_length=255, description="Reason for the assignment"
    )
    ai_session_id: Optional[uuid.UUID] = Field(
        default=None,
        description="AI session identifier if the assignment was performed by an AI agent",
    )


class TenantCreateTicketAssignment(TicketAssignmentBase):
    """Request model for creating a ticket assignment in a tenant context."""

    pass


class AdminCreateTicketAssignment(TicketAssignmentBase):
    """Request model for creating a ticket assignment via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the assignment")


class TicketAssignmentOut(BaseModel):
    """Response model representing a ticket assignment."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    assigned_group_id: Optional[uuid.UUID] = None
    assigned_user_id: Optional[uuid.UUID] = None
    assigned_by_user_id: Optional[uuid.UUID] = None
    assigned_by_reason: Optional[str] = None
    ai_session_id: Optional[uuid.UUID] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketAssignmentBase",
    "TenantCreateTicketAssignment",
    "AdminCreateTicketAssignment",
    "TicketAssignmentOut",
]