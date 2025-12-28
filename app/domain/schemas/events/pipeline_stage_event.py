"""
Event message schemas for pipeline stage lifecycle events.

Pipeline stages represent individual steps within a pipeline.  These
events are emitted whenever a stage is created, updated or deleted.
Downstream systems can subscribe to stage changes to update their
internal representation of workflows.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class PipelineStageBaseMessage(BaseModel):
    """Base fields common to all pipeline stage events."""

    tenant_id: UUID


class PipelineStageCreatedMessage(PipelineStageBaseMessage):
    """Event emitted when a pipeline stage is created."""

    payload: Dict[str, Any]


class PipelineStageUpdatedMessage(PipelineStageBaseMessage):
    """Event emitted when a pipeline stage is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class PipelineStageDeletedMessage(PipelineStageBaseMessage):
    """Event emitted when a pipeline stage is deleted."""

    deleted_dt: Optional[str] = None
