"""
Pydantic schemas for the StageHistory domain.

Stage history records capture transitions between pipeline stages for CRM entities.
These schemas define the structure for creation requests (internal use) and
read responses used by the API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class StageHistoryCreate(BaseModel):
    """Request model for recording a stage history entry."""

    entity_type: str = Field(
        ..., max_length=50, description="Entity type (e.g. deal, lead)"
    )
    entity_id: uuid.UUID = Field(
        ..., description="Identifier of the entity whose stage changed"
    )
    pipeline_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional pipeline identifier"
    )
    from_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Previous stage identifier"
    )
    to_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="New stage identifier"
    )
    changed_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when the stage change occurred; defaults to now",
    )
    changed_by_user_id: Optional[uuid.UUID] = Field(
        default=None, description="User who performed the change"
    )
    source: Optional[str] = Field(
        default=None, max_length=50, description="Optional source of the change"
    )


class StageHistoryRead(BaseModel):
    """Response model representing a stage history record."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    pipeline_id: Optional[uuid.UUID] = None
    from_stage_id: Optional[uuid.UUID] = None
    to_stage_id: Optional[uuid.UUID] = None
    changed_at: Optional[datetime] = None
    changed_by_user_id: Optional[uuid.UUID] = None
    source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = ["StageHistoryCreate", "StageHistoryRead"]