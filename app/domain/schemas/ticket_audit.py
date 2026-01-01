"""
Pydantic schemas for TicketAudit.

These models define response structures for viewing ticket audit events.
Audit events are append‑only and record changes to a ticket's state
along with actor information and before/after snapshots.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketAuditOut(BaseModel):
    """Response model representing a ticket audit entry."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    event_type: str
    actor_type: str
    actor_contact_id: Optional[uuid.UUID] = None
    actor_user_id: Optional[uuid.UUID] = None
    actor_display_name: Optional[str] = None
    ai_session_id: Optional[uuid.UUID] = None
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    occurred_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketAuditOut",
]