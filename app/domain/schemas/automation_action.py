"""
Pydantic schemas for automation actions.

Automation actions define workflows triggered by events on CRM records.  They
specify a scope (record, pipeline, stage or list), an event to trigger on,
optional conditions, an action type and configuration.  These schemas are
used by the API layer for validation and by services to convert between
models and external representations.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class AutomationActionBase(BaseModel):
    """Shared attributes for creating or updating automation actions."""

    entity_type: str = Field(..., max_length=50, description="Type of the entity that triggers the action")
    scope_type: str = Field(
        ..., max_length=30, description="Scope in which the action applies (RECORD, PIPELINE, PIPELINE_STAGE, LIST)"
    )
    record_type: Optional[str] = Field(
        default=None, max_length=50, description="Type of record when scope_type=RECORD"
    )
    record_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the record when scope_type=RECORD"
    )
    pipeline_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the pipeline when scope_type=PIPELINE"
    )
    pipeline_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the pipeline stage when scope_type=PIPELINE_STAGE"
    )
    list_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the list when scope_type=LIST"
    )
    trigger_event: Optional[str] = Field(
        default=None, max_length=100, description="Event that triggers the action"
    )
    condition_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional JSON expression used to filter events"
    )
    action_type: str = Field(
        ..., max_length=30, description="Type of action to perform"
    )
    config_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration for the action encoded as JSON"
    )
    priority: Optional[int] = Field(
        default=0, description="Priority used to order actions (higher executes earlier)"
    )
    enabled: Optional[bool] = Field(
        default=True, description="Whether the action is enabled"
    )
    inherit_pipeline_actions: Optional[bool] = Field(
        default=True,
        description="If true, actions defined on the pipeline are inherited by pipeline stages and lists",
    )


class AutomationActionCreate(AutomationActionBase):
    """Model for creating a new automation action."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the action")


class AutomationActionUpdate(BaseModel):
    """Model for updating an existing automation action.  All fields are optional."""

    entity_type: Optional[str] = Field(default=None, max_length=50)
    scope_type: Optional[str] = Field(default=None, max_length=30)
    record_type: Optional[str] = Field(default=None, max_length=50)
    record_id: Optional[uuid.UUID] = None
    pipeline_id: Optional[uuid.UUID] = None
    pipeline_stage_id: Optional[uuid.UUID] = None
    list_id: Optional[uuid.UUID] = None
    trigger_event: Optional[str] = Field(default=None, max_length=100)
    condition_json: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = Field(default=None, max_length=30)
    config_json: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    inherit_pipeline_actions: Optional[bool] = None


class AutomationActionRead(AutomationActionBase):
    """Model returned when reading an automation action."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "AutomationActionBase",
    "AutomationActionCreate",
    "AutomationActionUpdate",
    "AutomationActionRead",
]