"""
Event models for TicketAttachment lifecycle.

These classes define the payload structure for events emitted when
ticket attachments are created or deleted.  Attachments are
append‑only, so only creation and deletion events are supported.
Each event includes the tenant_id for routing and filtering by
downstream consumers.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketAttachmentDelta(BaseModel):
    """Delta describing changed fields on a ticket attachment (unused)."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of changed fields on the attachment",
    )


class TicketAttachmentCreatedEvent(BaseModel):
    """Event published when a ticket attachment is created."""

    tenant_id: uuid.UUID
    payload: Dict[str, Any]


class TicketAttachmentDeletedEvent(BaseModel):
    """Event published when a ticket attachment is deleted."""

    tenant_id: uuid.UUID
    deleted_dt: Optional[str] = Field(
        default=None, description="Timestamp when the deletion occurred"
    )


__all__ = [
    "TicketAttachmentDelta",
    "TicketAttachmentCreatedEvent",
    "TicketAttachmentDeletedEvent",
]