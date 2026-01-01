"""
Pydantic schemas for TicketMessage.

These models define the request and response structures for managing
messages on tickets.  A message represents a single entry in the
conversation thread of a ticket.  Messages are append‑only; there
are no update or delete operations exposed via the API.  Separate
request schemas exist for tenant and admin contexts; admin creation
requires specifying the tenant_id in the payload.  Response models
include audit fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class TicketMessageBase(BaseModel):
    """Shared attributes for creating a ticket message."""

    author_type: str = Field(
        ...,
        description="Type of message author: contact, agent, system, or ai",
        examples=["contact", "agent", "system", "ai"],
    )
    author_contact_id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "Identifier of the contact author when author_type is 'contact';"
            " ignored otherwise"
        ),
    )
    author_user_id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "Identifier of the user author when author_type is 'agent';"
            " ignored otherwise"
        ),
    )
    author_display_name: Optional[str] = Field(
        default=None,
        description="Display name of the author (optional; may override contact/user name)",
        max_length=255,
    )
    is_public: bool = Field(
        default=True,
        description="Whether the message is public (visible to requester) or internal",
    )
    channel_type: str = Field(
        default="internal",
        description="Channel through which the message was received or sent",
        examples=["email", "web", "chat", "sms", "voice", "api", "internal", "social"],
    )
    external_ref: Optional[str] = Field(
        default=None,
        description=(
            "Provider‑specific identifier for deduplication, such as an email message‑id"
        ),
        max_length=255,
    )
    subject: Optional[str] = Field(
        default=None,
        description="Optional subject line for the message",
        max_length=255,
    )
    body: str = Field(
        ...,
        description="Body of the message (plain text)",
    )
    # Renamed from `metadata` to avoid conflict with SQLAlchemy's reserved attribute
    provider_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Non‑secret provider payload snapshot stored as JSON",
    )


class TenantCreateTicketMessage(TicketMessageBase):
    """Request model for creating a ticket message in a tenant context."""

    pass


class AdminCreateTicketMessage(TicketMessageBase):
    """Request model for creating a ticket message via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the ticket message"
    )


class TicketMessageOut(BaseModel):
    """Response model representing a ticket message."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    author_type: str
    author_contact_id: Optional[uuid.UUID] = None
    author_user_id: Optional[uuid.UUID] = None
    author_display_name: Optional[str] = None
    is_public: bool
    channel_type: str
    external_ref: Optional[str] = None
    subject: Optional[str] = None
    body: str
    # Renamed from `metadata` to avoid conflict with SQLAlchemy's reserved attribute
    provider_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketMessageBase",
    "TenantCreateTicketMessage",
    "AdminCreateTicketMessage",
    "TicketMessageOut",
]