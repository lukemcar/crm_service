"""
Event models for TicketAudit lifecycle.

Audit events are append‑only and record changes to tickets.  These
classes define the payload structure for events emitted when a new
ticket audit entry is created.  Each event includes the tenant_id
for routing and filtering by downstream consumers.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict

from pydantic import BaseModel


class TicketAuditCreatedEvent(BaseModel):
    """Event published when a ticket audit entry is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


__all__ = [
    "TicketAuditCreatedEvent",
]