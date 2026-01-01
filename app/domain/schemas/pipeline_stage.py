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
    stage_order: int
    probability: Optional[float] = None


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageUpdate(BaseModel):
    pipeline_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=255)
    stage_order: Optional[int] = None
    probability: Optional[float] = None


class PipelineStageRead(PipelineStageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)