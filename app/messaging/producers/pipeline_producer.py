"""
Producer for pipeline lifecycle events.

Publishes events when pipelines are created, updated or deleted.
Pipelines define the ordering of stages for deals and tickets and
changes should be propagated to interested services.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    PipelineCreatedMessage,
    PipelineUpdatedMessage,
    PipelineDeletedMessage,
)
from .common import BaseProducer


class PipelineProducer(BaseProducer):
    """Producer for pipeline events."""

    @classmethod
    def publish_pipeline_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = PipelineCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.pipeline.created", message_model=message)

    @classmethod
    def publish_pipeline_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = PipelineUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.pipeline.updated", message_model=message)

    @classmethod
    def publish_pipeline_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = PipelineDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.pipeline.deleted", message_model=message)
