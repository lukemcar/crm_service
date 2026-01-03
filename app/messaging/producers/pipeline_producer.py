"""
Pipeline event producer for the CRM service.

This module defines a message producer class that publishes pipeline
lifecycle events to the CRM exchange via Celery.  Pipelines define
sequences of stages that deals and other workflows progress through.
The fully qualified task names derive from the global exchange name
(e.g. ``crm.pipeline.created``).  Messages are wrapped in Pydantic
models to ensure consistent schemas across producers and consumers.

``PipelineMessageProducer`` should be used by the service layer
(``pipeline_service.py``) to emit events after a successful
database commit.  Consumers can rely on these messages being sent
exactly once after the transaction has been committed.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.pipeline_event import (
    PipelineCreatedMessage,
    PipelineUpdatedMessage,
    PipelineDeletedMessage,
)
from .common import BaseProducer


class PipelineMessageProducer(BaseProducer):
    """Publishes pipeline lifecycle events via Celery.

    Task names are derived from the global ``EXCHANGE_NAME`` so that
    pipeline events share the same exchange as other CRM entities.
    Each event includes headers containing the tenant ID to aid in
    routing and filtering.  Clients should always prefer these
    ``send_*`` methods for publishing events.
    """

    TASK_CREATED: str = f"{EXCHANGE_NAME}.pipeline.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.pipeline.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.pipeline.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_pipeline_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``pipeline.created`` event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owns the pipeline.
        payload : dict
            Snapshot of the created pipeline.
        """
        message = PipelineCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_pipeline_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``pipeline.updated`` event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owns the pipeline.
        changes : dict
            Dictionary of changed fields and their new values.
        payload : dict
            Snapshot of the updated pipeline.
        """
        message = PipelineUpdatedMessage(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_pipeline_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ``pipeline.deleted`` event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owned the pipeline.
        deleted_dt : str | None
            ISO 8601 timestamp indicating when the deletion occurred.
            If omitted, consumers may use the message processing timestamp.
        """
        message = PipelineDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


# Backwards compatibility alias
PipelineProducer = PipelineMessageProducer