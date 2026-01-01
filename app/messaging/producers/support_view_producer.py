"""
Producer for support view lifecycle events.

This module encapsulates the publishing logic for support view events.
Task names follow the ``<exchange>.support_view.<action>`` convention
consistent with other domain producers.  Events are published after
successful database mutations in the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.support_view_event import (
    SupportViewCreatedEvent,
    SupportViewUpdatedEvent,
    SupportViewDeletedEvent,
    SupportViewDelta,
)
from .common import BaseProducer


class SupportViewMessageProducer(BaseProducer):
    """Publishes support view lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.support_view.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.support_view.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.support_view.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_support_view_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a support_view.created event."""
        message = SupportViewCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_support_view_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: SupportViewDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a support_view.updated event."""
        message = SupportViewUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_support_view_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a support_view.deleted event."""
        message = SupportViewDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "SupportViewMessageProducer",
]