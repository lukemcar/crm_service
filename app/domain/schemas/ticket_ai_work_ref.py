"""
Pydantic schemas for TicketAiWorkRef.

These models define request and response structures for linking tickets
to AI Workforce sessions. Each record stores metadata about an AI
session used to process the ticket, including agent key, purpose,
status, outcome, and confidence. The records are typically read-only
for tenants; admin or internal APIs may upsert entries.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketAiWorkRefBase(BaseModel):
    """Shared attributes for a ticket AI work reference upsert."""

    ticket_id: uuid.UUID = Field(
        ..., description="Identifier of the ticket this AI session relates to"
    )
    ai_session_id: uuid.UUID = Field(
        ..., description="Unique AI session identifier from the AI Workforce service"
    )
    agent_key: str = Field(
        ..., max_length=120, description="Agent key representing the AI agent"
    )
    purpose: str = Field(
        ..., max_length=100, description="Purpose of the AI session (e.g. triage)"
    )
    status: Optional[str] = Field(
        default="started", max_length=50, description="Status of the AI session"
    )
    outcome: Optional[str] = Field(
        default=None, max_length=50, description="Outcome of the AI session"
    )
    confidence: Optional[float] = Field(
        default=None, description="Confidence score for the AI session"
    )
    requested_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the AI session was requested in ISO 8601 format",
    )
    completed_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the AI session completed in ISO 8601 format",
    )
    created_by: Optional[str] = Field(
        default=None, description="Identifier of who created this record"
    )


class AdminUpsertTicketAiWorkRef(TicketAiWorkRefBase):
    """Request model for upserting a ticket AI work reference via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the AI work reference"
    )
    id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "Unique identifier for the AI work reference. "
            "If omitted, a new record will be created."
        ),
    )


class TicketAiWorkRefOut(BaseModel):
    """Response model representing a ticket AI work reference."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    ai_session_id: uuid.UUID
    agent_key: str
    purpose: str
    status: str
    outcome: Optional[str] = None
    confidence: Optional[float] = None
    requested_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketAiWorkRefBase",
    "AdminUpsertTicketAiWorkRef",
    "TicketAiWorkRefOut",
]