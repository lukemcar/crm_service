"""
Event message schemas for pipeline lifecycle events.

Pipelines define the ordering of stages for deals, tickets and other
workflows.  These events communicate changes to pipeline definitions
across the platform.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class PipelineBaseMessage(BaseModel):
    """Base fields common to all pipeline events."""

    tenant_id: UUID


class PipelineCreatedMessage(PipelineBaseMessage):
    """Event emitted when a pipeline is created."""

    payload: Dict[str, Any]


class PipelineUpdatedMessage(PipelineBaseMessage):
    """Event emitted when a pipeline is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class PipelineDeletedMessage(PipelineBaseMessage):
    """Event emitted when a pipeline is deleted."""

    deleted_dt: Optional[str] = None
