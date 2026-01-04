"""Pydantic schemas for PipelineStage.

Stages belong to a pipeline and define the progression of deals or tickets.
These schemas specify create, update and read forms for stages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PipelineStageBase(BaseModel):
    pipeline_id: Optional[UUID]
    name: str = Field(..., max_length=255)
    # display_order replaces stage_order from the original schema
    display_order: int = Field(
        ..., description="Position of the stage within its pipeline"
    )
    probability: Optional[float] = Field(
        default=None,
        description="Probability value between 0 and 1; None if not applicable",
    )
    stage_state: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Current state of the stage (e.g., NOT_STARTED, ACTIVE, WON, LOST)",
    )
    inherit_pipeline_actions: Optional[bool] = Field(
        default=None,
        description="Whether this stage inherits automation actions from the parent pipeline",
    )


class PipelineStageCreate(PipelineStageBase):
    """Schema for creating a pipeline stage."""
    pass


class PipelineStageUpdate(BaseModel):
    pipeline_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=255)
    display_order: Optional[int] = Field(
        None, description="Position of the stage within its pipeline"
    )
    probability: Optional[float] = Field(
        None,
        description="Probability value between 0 and 1; None if not applicable",
    )
    stage_state: Optional[str] = Field(
        None,
        max_length=30,
        description="Current state of the stage (e.g., NOT_STARTED, ACTIVE, WON, LOST)",
    )
    inherit_pipeline_actions: Optional[bool] = Field(
        None,
        description="Whether this stage inherits automation actions from the parent pipeline",
    )


class PipelineStageRead(PipelineStageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)