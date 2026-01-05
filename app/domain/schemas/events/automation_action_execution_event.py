"""
Event schemas for AutomationActionExecution status changes.

These Pydantic models define the payload for events emitted when the status
of an automation action execution record changes.  Downstream consumers
can subscribe to these events to monitor execution progress and outcomes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AutomationActionExecutionStatusChangedEvent(BaseModel):
    """Payload for an automation_action_execution.status_changed event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    execution_id: UUID = Field(..., description="Execution record identifier")
    action_id: UUID = Field(..., description="Automation action identifier")
    status: str = Field(..., description="New status of the execution")
    payload: Dict[str, Any] = Field(
        ..., description="Full execution snapshot after the status change"
    )
    changed_dt: Optional[str] = Field(
        None, description="ISO timestamp when the status change occurred"
    )


__all__ = ["AutomationActionExecutionStatusChangedEvent"]