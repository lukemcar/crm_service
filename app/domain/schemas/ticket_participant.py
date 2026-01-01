"""
Pydantic schemas for TicketParticipant.

These models define the request and response structures for managing
ticket participants.  Participants may be contacts or agents and
carry a role indicating their relationship to the ticket (requester,
CC, follower).  Separate request schemas exist for tenant and
admin contexts; admin creation requires specifying the tenant_id in
the payload.  Response models include audit fields and mirror the
ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketParticipantBase(BaseModel):
    """Shared attributes for creating a ticket participant."""

    participant_type: str = Field(
        ...,
        description="Type of participant: 'contact' or 'agent'",
        examples=["contact", "agent"],
    )
    role: Optional[str] = Field(
        "cc",
        description="Role of the participant on the ticket: requester, cc, or follower",
        examples=["requester", "cc", "follower"],
    )
    contact_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the contact participant (if participant_type = contact)"
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the user participant (if participant_type = agent)"
    )


class TenantCreateTicketParticipant(TicketParticipantBase):
    """Request model for creating a ticket participant in a tenant context."""

    pass


class AdminCreateTicketParticipant(TicketParticipantBase):
    """Request model for creating a ticket participant via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the ticket participant"
    )


class TicketParticipantOut(BaseModel):
    """Response model representing a ticket participant."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    participant_type: str
    contact_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    role: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketParticipantBase",
    "TenantCreateTicketParticipant",
    "AdminCreateTicketParticipant",
    "TicketParticipantOut",
]