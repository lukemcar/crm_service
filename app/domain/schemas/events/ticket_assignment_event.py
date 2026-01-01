"""
Event models for TicketAssignment lifecycle.

These classes define the payload structure for events emitted when
ticket assignments are created.  Assignments are append‑only;
updates and deletions are not supported.
Each event includes the tenant_id for routing and filtering by
downstream consumers.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketAssignmentDelta(BaseModel):
    """Delta describing changed fields on a ticket assignment (unused)."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of changed fields on the assignment",
    )


class TicketAssignmentCreatedEvent(BaseModel):
    """Event published when a ticket assignment is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


__all__ = [
    "TicketAssignmentDelta",
    "TicketAssignmentCreatedEvent",
]