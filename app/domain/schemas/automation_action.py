"""
Pydantic schemas for the AutomationAction domain.

Automation actions define declarative rules that perform an action when a
specified trigger occurs.  Each automation action targets exactly one
context: either a specific record, a pipeline, a pipeline stage or a list.
This module defines the create, update and read schemas for these actions
along with validation to ensure only one target is provided.  Defaults are
supplied for priority, enabled and inherit_pipeline_actions as described in
the consolidated CRM change request guide【480489992503603†L220-L224】.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


class AutomationActionBase(BaseModel):
    """Shared attributes for automation actions used in creation and update.

    Exactly one of the target fields (record_id, pipeline_id,
    pipeline_stage_id, list_id) must be provided.  This requirement
    mirrors the scope check constraint enforced at the database layer
    described in the implementation guide【480489992503603†L220-L224】.
    """

    entity_type: str = Field(..., max_length=50, description="CRM entity type this rule applies to")
    scope_type: str = Field(..., max_length=50, description="Scope type determining which target column is used")
    record_type: Optional[str] = Field(
        default=None, max_length=50, description="CRM record type when targeting a specific record"
    )
    record_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the record when targeting a specific record"
    )
    pipeline_id: Optional[uuid.UUID] = Field(
        default=None, description="Pipeline identifier when targeting a pipeline"
    )
    pipeline_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Pipeline stage identifier when targeting a stage"
    )
    list_id: Optional[uuid.UUID] = Field(
        default=None, description="List identifier when targeting a list"
    )
    trigger_event: str = Field(..., max_length=100, description="Event that triggers this action")
    condition_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional JSON condition specifying when the action runs"
    )
    action_type: str = Field(..., max_length=100, description="Type of action to perform")
    config_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration parameters for the action"
    )
    priority: Optional[int] = Field(
        default=1, ge=1, description="Execution priority; lower numbers run first"
    )
    enabled: Optional[bool] = Field(
        default=True, description="Whether the action is enabled"
    )
    inherit_pipeline_actions: Optional[bool] = Field(
        default=True,
        description="Whether pipeline actions should be inherited when targeting a stage",
    )

    @model_validator(mode="after")
    def check_target(cls, values: "AutomationActionBase") -> "AutomationActionBase":
        """Ensure exactly one target field is provided.

        The automation_action table enforces a check constraint that one and only
        one of the target columns (record_id, pipeline_id, pipeline_stage_id,
        list_id) is non-null.  This validator mirrors that constraint at the
        application layer to surface validation errors early.
        """
        target_fields = [
            values.record_id,
            values.pipeline_id,
            values.pipeline_stage_id,
            values.list_id,
        ]
        provided = [f for f in target_fields if f is not None]
        if len(provided) != 1:
            raise ValueError(
                "Exactly one of record_id, pipeline_id, pipeline_stage_id or list_id must be provided"
            )
        return values


class AutomationActionCreate(AutomationActionBase):
    """Request model for creating an automation action via tenant or admin APIs.

    The tenant_id is supplied externally (path parameter or explicit field in
    the admin context) rather than as part of this schema.  Audit fields are
    handled by the service layer and are not exposed here.
    """

    pass


class AutomationActionUpdate(BaseModel):
    """Request model for updating an existing automation action.

    All fields are optional; only those provided will be updated.  The same
    single-target validation rules apply.  If any target field is supplied,
    exactly one must be non-null, otherwise the existing values are retained.
    """

    entity_type: Optional[str] = Field(
        default=None, max_length=50, description="CRM entity type this rule applies to"
    )
    scope_type: Optional[str] = Field(
        default=None, max_length=50, description="Scope type determining which target column is used"
    )
    record_type: Optional[str] = Field(
        default=None, max_length=50, description="CRM record type when targeting a specific record"
    )
    record_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the record when targeting a specific record"
    )
    pipeline_id: Optional[uuid.UUID] = Field(
        default=None, description="Pipeline identifier when targeting a pipeline"
    )
    pipeline_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Pipeline stage identifier when targeting a stage"
    )
    list_id: Optional[uuid.UUID] = Field(
        default=None, description="List identifier when targeting a list"
    )
    trigger_event: Optional[str] = Field(
        default=None, max_length=100, description="Event that triggers this action"
    )
    condition_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional JSON condition specifying when the action runs"
    )
    action_type: Optional[str] = Field(
        default=None, max_length=100, description="Type of action to perform"
    )
    config_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration parameters for the action"
    )
    priority: Optional[int] = Field(
        default=None, ge=1, description="Execution priority; lower numbers run first"
    )
    enabled: Optional[bool] = Field(
        default=None, description="Whether the action is enabled"
    )
    inherit_pipeline_actions: Optional[bool] = Field(
        default=None,
        description="Whether pipeline actions should be inherited when targeting a stage",
    )

    @model_validator(mode="after")
    def check_update_target(cls, values: "AutomationActionUpdate") -> "AutomationActionUpdate":
        """Enforce that at most one target field is provided on update.

        When updating an action's scope, exactly one of the target fields must be
        provided if any are set; otherwise, all target fields should be omitted
        to leave the existing target unchanged.
        """
        target_fields = [
            values.record_id,
            values.pipeline_id,
            values.pipeline_stage_id,
            values.list_id,
        ]
        provided = [f for f in target_fields if f is not None]
        if provided and len(provided) != 1:
            raise ValueError(
                "When updating targets, exactly one of record_id, pipeline_id, pipeline_stage_id or list_id must be provided"
            )
        return values


class AutomationActionRead(AutomationActionBase):
    """Response model for an automation action.

    Exposes all persisted fields, including audit and tenant identifiers.  The
    model is configured to load from ORM objects via ``from_attributes`` so
    that SQLAlchemy instances can be validated directly.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: Optional[str] = Field(default=None, description="ISO timestamp when created")
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp when last updated")
    created_by_user_id: Optional[str] = Field(default=None, description="User ID who created the action")
    updated_by_user_id: Optional[str] = Field(default=None, description="User ID who last updated the action")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "AutomationActionCreate",
    "AutomationActionUpdate",
    "AutomationActionRead",
]