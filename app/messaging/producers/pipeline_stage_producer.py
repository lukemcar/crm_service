"""
Pipeline stage event producer for the CRM service.

This module defines a message producer class that publishes pipeline
stage lifecycle events to the CRM exchange via Celery.  Stages
belong to pipelines and define the progression of deals or tickets.  The
fully qualified task names derive from the global exchange name
(e.g. ``crm.pipeline_stage.created``).  Messages are wrapped in
Pydantic models to ensure consistent schemas across producers and
consumers.

``PipelineStageMessageProducer`` should be used by the service layer
(``pipeline_stage_service.py``) to emit events after a successful
database commit.  Consumers can rely on these messages being sent
exactly once after the transaction has been committed.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.pipeline_stage_event import (
    PipelineStageCreatedMessage,
    PipelineStageUpdatedMessage,
    PipelineStageDeletedMessage,
)
from .common import BaseProducer


class PipelineStageMessageProducer(BaseProducer):
    """Publishes pipeline stage lifecycle events via Celery.

    Task names are derived from the global ``EXCHANGE_NAME`` so that
    pipeline stage events share the same exchange as other CRM
    entities.  Each event includes headers containing the tenant ID
    to aid in routing and filtering.  Clients should always prefer
    these ``send_*`` methods for publishing events.
    """

    TASK_CREATED: str = f"{EXCHANGE_NAME}.pipeline_stage.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.pipeline_stage.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.pipeline_stage.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_stage_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``pipeline_stage.created`` event."""
        message = PipelineStageCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_stage_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``pipeline_stage.updated`` event."""
        message = PipelineStageUpdatedMessage(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_stage_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ``pipeline_stage.deleted`` event."""
        message = PipelineStageDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


# Backwards compatibility alias
PipelineStageProducer = PipelineStageMessageProducer