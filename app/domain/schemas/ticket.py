"""
Pydantic schemas for the Ticket domain.

These models define request and response structures used when
creating, updating and retrieving tickets.  Separate models exist
for tenant and admin creation to enforce explicit tenant scoping.
Response models include audit fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketBase(BaseModel):
    """Shared attributes for ticket creation and update."""

    subject: str = Field(..., max_length=255, description="Short summary of the ticket")
    description: Optional[str] = Field(
        default=None, description="Detailed description or initial body of the ticket"
    )
    status: Optional[str] = Field(
        default="new",
        description="Ticket status (new, open, pending, on_hold, solved, closed)",
    )
    priority: Optional[str] = Field(
        default="normal",
        description="Ticket priority (low, normal, high, urgent)",
    )
    ticket_type: Optional[str] = Field(
        default="question",
        description="Ticket type (question, incident, problem, task)",
    )
    assigned_group_id: Optional[uuid.UUID] = Field(
        default=None, description="Group to which the ticket is assigned"
    )
    assigned_user_id: Optional[uuid.UUID] = Field(
        default=None, description="User to which the ticket is assigned"
    )
    inbound_channel_id: Optional[uuid.UUID] = Field(
        default=None, description="Inbound channel through which the ticket was created"
    )
    ticket_form_id: Optional[uuid.UUID] = Field(
        default=None, description="Form definition used to capture custom fields"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None, description="Arbitrary custom fields attached to the ticket"
    )
    work_mode: Optional[str] = Field(
        default="human_only",
        description="AI work mode (human_only, ai_allowed, ai_preferred, ai_only)",
    )


class TenantCreateTicket(TicketBase):
    """Request model for creating a ticket in a tenant context."""

    requester_contact_id: Optional[uuid.UUID] = Field(
        default=None, description="Contact who requested the ticket"
    )
    company_id: Optional[uuid.UUID] = Field(
        default=None, description="Company associated with the ticket"
    )


class AdminCreateTicket(TicketBase):
    """Request model for creating a ticket via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the ticket"
    )
    requester_contact_id: Optional[uuid.UUID] = Field(
        default=None, description="Contact who requested the ticket"
    )
    company_id: Optional[uuid.UUID] = Field(
        default=None, description="Company associated with the ticket"
    )


class TicketUpdate(BaseModel):
    """Request model for updating an existing ticket."""

    subject: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None)
    ticket_type: Optional[str] = Field(default=None)
    assigned_group_id: Optional[uuid.UUID] = Field(default=None)
    assigned_user_id: Optional[uuid.UUID] = Field(default=None)
    inbound_channel_id: Optional[uuid.UUID] = Field(default=None)
    ticket_form_id: Optional[uuid.UUID] = Field(default=None)
    custom_fields: Optional[Dict[str, Any]] = Field(default=None)
    work_mode: Optional[str] = Field(default=None)


class TicketOut(BaseModel):
    """Response model representing a ticket."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    requester_contact_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    inbound_channel_id: Optional[uuid.UUID] = None
    ticket_form_id: Optional[uuid.UUID] = None
    subject: str
    description: Optional[str] = None
    status: str
    priority: str
    ticket_type: str
    assigned_group_id: Optional[uuid.UUID] = None
    assigned_user_id: Optional[uuid.UUID] = None
    first_response_at: Optional[str] = None
    last_message_at: Optional[str] = None
    solved_at: Optional[str] = None
    closed_at: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    orchestration_workflow_key: Optional[str] = None
    orchestration_instance_id: Optional[str] = None
    orchestration_state: Optional[Dict[str, Any]] = None
    work_mode: str
    ai_status: str
    ai_last_session_id: Optional[uuid.UUID] = None
    ai_last_agent_key: Optional[str] = None
    ai_last_outcome: Optional[str] = None
    ai_last_confidence: Optional[float] = None
    ai_last_completed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketBase",
    "TenantCreateTicket",
    "AdminCreateTicket",
    "TicketUpdate",
    "TicketOut",
]