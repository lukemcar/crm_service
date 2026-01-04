"""Pydantic schemas for Pipeline.

Pipelines group stages for deals and tickets.  Each pipeline is scoped
to a tenant and has a name.  These schemas define create, update and
read representations for pipelines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PipelineBase(BaseModel):
    """Shared fields for pipeline create and update operations."""

    name: str = Field(..., max_length=255)
    object_type: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Type of objects managed by this pipeline (e.g., DEAL, TICKET)"
    )
    display_order: Optional[int] = Field(
        default=None,
        description="Order of this pipeline among pipelines of the same object type"
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Whether the pipeline is active"
    )
    pipeline_key: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Stable unique key for API clients to reference this pipeline"
    )
    movement_mode: Optional[str] = Field(
        default="FLEXIBLE",
        max_length=30,
        description="Movement enforcement mode for pipeline"
    )


class PipelineCreate(PipelineBase):
    tenant_id: UUID = Field(..., description="Tenant identifier for the pipeline")

    # ``object_type`` is required on creation; set default in service if omitted
    object_type: str = Field(
        ..., max_length=30, description="Type of objects managed by this pipeline"
    )
    # ``display_order``, ``pipeline_key`` are assigned by the service if not provided


class PipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    object_type: Optional[str] = Field(None, max_length=30)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    pipeline_key: Optional[str] = Field(None, max_length=100)
    movement_mode: Optional[str] = Field(None, max_length=30)


class PipelineRead(PipelineBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Expose assigned fields on read
    object_type: str
    display_order: int
    is_active: bool
    pipeline_key: str
    movement_mode: str

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)