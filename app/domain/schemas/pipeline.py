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
    name: str = Field(..., max_length=255)


class PipelineCreate(PipelineBase):
    pass


class PipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)


class PipelineRead(PipelineBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)