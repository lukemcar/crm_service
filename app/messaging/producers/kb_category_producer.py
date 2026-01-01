"""
Producer for knowledge base category lifecycle events.

This module encapsulates the publishing logic for KB category events.
Task names follow the ``<exchange>.kb_category.<action>`` convention
consistent with other domain producers.  Events are published after
successful database mutations in the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.kb_category_event import (
    KbCategoryCreatedEvent,
    KbCategoryUpdatedEvent,
    KbCategoryDeletedEvent,
    KbCategoryDelta,
)
from .common import BaseProducer


class KbCategoryMessageProducer(BaseProducer):
    """Publishes knowledge base category lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.kb_category.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.kb_category.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.kb_category.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_kb_category_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a kb_category.created event."""
        message = KbCategoryCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_category_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: KbCategoryDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a kb_category.updated event."""
        message = KbCategoryUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_category_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a kb_category.deleted event."""
        message = KbCategoryDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "KbCategoryMessageProducer",
]