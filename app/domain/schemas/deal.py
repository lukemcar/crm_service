"""Pydantic schemas for Deal.

Deals represent sales opportunities and reference a pipeline and stage.
These schemas separate create, update and read models for deals.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class DealBase(BaseModel):
    name: str = Field(..., max_length=255)
    amount: Optional[float] = None
    expected_close_date: Optional[date] = None
    pipeline_id: UUID
    stage_id: UUID
    probability: Optional[float] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    amount: Optional[float] = None
    expected_close_date: Optional[date] = None
    pipeline_id: Optional[UUID] = None
    stage_id: Optional[UUID] = None
    probability: Optional[float] = None


class DealRead(DealBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Configure Pydantic v2 to load from ORM attributes
    model_config = ConfigDict(from_attributes=True)