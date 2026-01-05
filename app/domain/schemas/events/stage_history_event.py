"""
Event message schema for stage history entries.

When a CRM entity transitions from one pipeline stage to another, a stage
history record is created.  This event payload captures the full snapshot
of the stage history so downstream systems can update metrics or timelines.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class StageHistoryCreatedEvent(BaseModel):
    """Payload for a stage_history.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full snapshot of the created stage history entry"
    )


__all__ = ["StageHistoryCreatedEvent"]