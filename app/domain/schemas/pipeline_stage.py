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
    """Base schema for pipeline stage creation and update.

    Includes the pipeline identifier, stage name, ordering, state,
    inheritance flag and probability.  Probability values must be between
    0 and 1 or omitted.  Ordering defaults are assigned in the service
    layer when not provided.
    """

    pipeline_id: Optional[UUID]
    name: str = Field(..., max_length=255)
    display_order: int = Field(..., description="Relative ordering of the stage within its pipeline")
    stage_state: Optional[str] = Field(None, description="Initial state of the stage")
    inherit_pipeline_actions: Optional[bool] = Field(None, description="Whether to inherit actions from the pipeline")
    probability: Optional[float] = None


class PipelineStageCreate(PipelineStageBase):
    """Schema for creating a pipeline stage.

    All fields are required except stage_state and inherit_pipeline_actions, which default
    to ``NOT_STARTED`` and ``True`` respectively when omitted.
    """
    pass


class PipelineStageUpdate(BaseModel):
    """Schema for updating an existing pipeline stage.

    All fields are optional; only provided fields will be updated.
    """

    pipeline_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=255)
    display_order: Optional[int] = None
    stage_state: Optional[str] = None
    inherit_pipeline_actions: Optional[bool] = None
    probability: Optional[float] = None


class PipelineStageRead(PipelineStageBase):
    """Read schema for pipeline stages.

    Extends the base fields with identifiers and audit metadata.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)