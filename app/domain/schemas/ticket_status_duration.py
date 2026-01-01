"""
Pydantic schemas for ticket status duration facts.

These schemas define request and response structures for the
``TicketStatusDuration`` domain.  Tenant endpoints provide read
access only, while admin endpoints can create, update, and delete
records for backfilling purposes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketStatusDurationBase(BaseModel):
    """Base fields for ticket status duration requests."""

    ticket_id: UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)


class AdminCreateTicketStatusDuration(TicketStatusDurationBase):
    """Schema for admin creation of ticket status durations."""

    tenant_id: UUID


class AdminUpdateTicketStatusDuration(BaseModel):
    """Schema for updating a ticket status duration record."""

    status: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)


class TicketStatusDurationOut(BaseModel):
    """Response schema for ticket status duration records."""

    id: UUID
    tenant_id: UUID
    ticket_id: UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    created_at: datetime
    created_by: Optional[str]

    model_config = {
        "from_attributes": True
    }


__all__ = [
    "TicketStatusDurationBase",
    "AdminCreateTicketStatusDuration",
    "AdminUpdateTicketStatusDuration",
    "TicketStatusDurationOut",
]