"""
Pydantic schemas for automation action execution records.

These schemas define the inputs and outputs for the automation action
execution API and service layer.  Executions record the outcome of
automation actions running on CRM records.  They include context
information such as the target entity, optional pipeline and stage
identifiers, a unique execution key for idempotency, and the status
of the execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class AutomationActionExecutionBase(BaseModel):
    """Shared attributes for creating or updating automation action executions."""

    action_id: uuid.UUID = Field(..., description="Identifier of the automation action that triggered this execution")
    entity_type: str = Field(..., max_length=50, description="Type of the entity involved in the execution")
    entity_id: uuid.UUID = Field(..., description="Identifier of the entity involved in the execution")
    pipeline_id: Optional[uuid.UUID] = Field(default=None, description="Pipeline identifier when applicable")
    from_stage_id: Optional[uuid.UUID] = Field(default=None, description="Previous stage identifier when applicable")
    to_stage_id: Optional[uuid.UUID] = Field(default=None, description="Target stage identifier when applicable")
    list_id: Optional[uuid.UUID] = Field(default=None, description="List identifier when applicable")
    trigger_event: Optional[str] = Field(default=None, max_length=100, description="Event that triggered the execution")
    execution_key: str = Field(..., max_length=255, description="Unique key to enforce idempotency for this execution")
    status: str = Field(..., max_length=30, description="Status of the execution (PENDING, IN_PROGRESS, SUCCEEDED, FAILED)")
    response_code: Optional[int] = Field(default=None, description="Optional HTTP or system response code")
    response_body: Optional[Dict[str, Any]] = Field(default=None, description="Optional response payload")
    error_message: Optional[str] = Field(default=None, max_length=255, description="Optional error message if execution failed")
    triggered_at: Optional[datetime] = Field(default=None, description="Timestamp when the execution was triggered")
    started_at: Optional[datetime] = Field(default=None, description="Timestamp when processing started")
    completed_at: Optional[datetime] = Field(default=None, description="Timestamp when processing completed")


class AutomationActionExecutionCreate(AutomationActionExecutionBase):
    """Model for creating a new automation action execution."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the execution")

    # When creating an execution, status defaults to PENDING if not provided
    status: str = Field(default="PENDING")


class AutomationActionExecutionUpdate(BaseModel):
    """Model for updating an existing execution.  All fields are optional."""

    status: Optional[str] = Field(default=None, max_length=30)
    response_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = Field(default=None, max_length=255)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AutomationActionExecutionRead(AutomationActionExecutionBase):
    """Model returned when reading an automation action execution."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "AutomationActionExecutionBase",
    "AutomationActionExecutionCreate",
    "AutomationActionExecutionUpdate",
    "AutomationActionExecutionRead",
]