"""
Pydantic schemas for ticket metrics.

These schemas define the request and response payloads for the
``TicketMetrics`` domain.  Tenant endpoints expose only read
operations; admin endpoints can create, update, and delete metrics
records.  The ``reply_count`` and ``reopen_count`` fields default to
zero if not provided.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketMetricsBase(BaseModel):
    """Base fields for ticket metrics requests."""

    ticket_id: UUID
    reply_count: int = Field(0, ge=0)
    reopen_count: int = Field(0, ge=0)


class AdminCreateTicketMetrics(TicketMetricsBase):
    """Schema for admin creation of ticket metrics."""

    tenant_id: UUID


class TicketMetricsUpdate(BaseModel):
    """Schema for updating ticket metrics."""

    reply_count: Optional[int] = Field(None, ge=0)
    reopen_count: Optional[int] = Field(None, ge=0)


class TicketMetricsOut(BaseModel):
    """Response schema for ticket metrics records."""

    id: UUID
    tenant_id: UUID
    ticket_id: UUID
    reply_count: int
    reopen_count: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str]

    model_config = {
        "from_attributes": True
    }


__all__ = [
    "TicketMetricsBase",
    "AdminCreateTicketMetrics",
    "TicketMetricsUpdate",
    "TicketMetricsOut",
]