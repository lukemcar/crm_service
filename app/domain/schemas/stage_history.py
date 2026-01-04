"""
Pydantic schemas for stage history entries.

These models define the structures used by the API and service layers
to create and retrieve stage history records.  A stage history
represents a transition of an entity between stages of a pipeline and
includes metadata about who initiated the change and when it occurred.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StageHistoryBase(BaseModel):
    """Shared attributes for creating or updating stage history records."""

    entity_type: str = Field(..., max_length=50, description="Type of the CRM entity (e.g., DEAL, LEAD)")
    entity_id: uuid.UUID = Field(..., description="Identifier of the entity that changed stages")
    pipeline_id: Optional[uuid.UUID] = Field(
        default=None, description="Optional identifier of the pipeline associated with the change"
    )
    from_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the previous stage, if any"
    )
    to_stage_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the new stage, if any"
    )
    changed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the stage change occurred; defaults to now"
    )
    changed_by_user_id: Optional[uuid.UUID] = Field(
        default=None, description="User ID of the person who initiated the change"
    )
    source: Optional[str] = Field(
        default=None, max_length=50, description="Optional string describing the source of the change"
    )


class StageHistoryCreate(StageHistoryBase):
    """Model for creating a stage history entry."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the history entry")
    # ``changed_at`` will default to current timestamp when the record is persisted


class StageHistoryRead(StageHistoryBase):
    """Model returned when reading a stage history entry."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    # ``changed_at`` will always be populated on read

    model_config = ConfigDict(from_attributes=True)


__all__ = ["StageHistoryCreate", "StageHistoryRead"]