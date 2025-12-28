"""
Producer for pipeline stage lifecycle events.

Emits events when pipeline stages are created, updated or deleted.
Pipeline stages belong to pipelines and changes must be propagated to
subscribers to maintain workflow state.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    PipelineStageCreatedMessage,
    PipelineStageUpdatedMessage,
    PipelineStageDeletedMessage,
)
from .common import BaseProducer


class PipelineStageProducer(BaseProducer):
    """Producer for pipeline stage events."""

    @classmethod
    def publish_stage_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = PipelineStageCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.pipeline_stage.created", message_model=message)

    @classmethod
    def publish_stage_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = PipelineStageUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.pipeline_stage.updated", message_model=message)

    @classmethod
    def publish_stage_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = PipelineStageDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.pipeline_stage.deleted", message_model=message)
