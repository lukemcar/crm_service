"""
Pydantic schemas for the AutomationActionExecution domain.

Execution records log each invocation of an automation action.  A record
contains the target entity context, a unique execution key, the current
status and optional response or error details.  Creation schemas are
intended for internal use by the automation engine and include only
the fields necessary to record an execution.  Read schemas expose all
fields for monitoring and diagnostics【480489992503603†L343-L367】.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class AutomationActionExecutionCreate(BaseModel):
    """Request model for creating an automation action execution record.

    The tenant_id and action_id are supplied externally.  The execution_key
    must be unique per tenant and is used to ensure idempotency of
    execution logging.  Status is not accepted on creation; it will be
    defaulted to ``PENDING`` by the service layer.
    """

    entity_type: str = Field(..., max_length=50, description="Entity type of the context")
    entity_id: uuid.UUID = Field(..., description="Identifier of the entity being acted upon")
    pipeline_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional pipeline identifier when relevant"
    )
    from_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional previous stage identifier when relevant"
    )
    to_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional next stage identifier when relevant"
    )
    list_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional list identifier when relevant"
    )
    trigger_event: str = Field(..., max_length=100, description="Event that triggered this execution")
    execution_key: str = Field(..., max_length=100, description="Unique execution key for idempotency")
    response_code: Optional[int] = Field(
        default=None, description="HTTP or application response code returned by the action"
    )
    response_body: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional response payload returned by the action"
    )
    error_message: Optional[str] = Field(
        default=None, max_length=500, description="Error message if the action failed"
    )
    triggered_at: Optional[str] = Field(
        default=None, description="ISO timestamp of when the execution was triggered"
    )
    started_at: Optional[str] = Field(
        default=None, description="ISO timestamp of when execution started"
    )
    completed_at: Optional[str] = Field(
        default=None, description="ISO timestamp of when execution completed"
    )


class AutomationActionExecutionRead(BaseModel):
    """Response model representing an automation action execution record."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    action_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    pipeline_id: Optional[uuid.UUID] = None
    from_stage_id: Optional[uuid.UUID] = None
    to_stage_id: Optional[uuid.UUID] = None
    list_id: Optional[uuid.UUID] = None
    trigger_event: str
    execution_key: str
    status: str
    response_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    triggered_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "AutomationActionExecutionCreate",
    "AutomationActionExecutionRead",
]