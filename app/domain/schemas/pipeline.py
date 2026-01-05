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
    """Base schema for Pipeline create/update operations.

    The base fields include the pipeline name and object type.  Additional
    optional fields (display order, active state, key, movement mode) are
    provided on the create and update schemas.  Validation on these fields
    occurs in the service layer rather than the schema itself.
    """

    name: str = Field(..., max_length=255)
    object_type: str = Field(..., max_length=50)


class PipelineCreate(PipelineBase):
    """Schema for creating a pipeline.

    Optional fields allow callers to specify ordering, activation state,
    key and movement mode.  Defaults will be applied by the service
    layer if omitted.
    """

    display_order: Optional[int] = None
    is_active: Optional[bool] = True
    pipeline_key: Optional[str] = None
    movement_mode: Optional[str] = None


class PipelineUpdate(BaseModel):
    """Schema for updating an existing pipeline.

    All fields are optional.  Only provided fields will be updated.
    """

    name: Optional[str] = Field(None, max_length=255)
    object_type: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    pipeline_key: Optional[str] = None
    movement_mode: Optional[str] = None


class PipelineRead(PipelineBase):
    """Read schema for pipelines.

    Exposes all persistent fields including the auto‑assigned key,
    movement mode and activation status.  Uses ``from_attributes=True`` to
    map SQLAlchemy ORM instances.
    """

    id: UUID
    tenant_id: UUID
    display_order: int
    is_active: bool
    pipeline_key: str
    movement_mode: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)