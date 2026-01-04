"""
Record watcher event producer for the CRM service.

This module defines a message producer class that publishes record
watcher lifecycle events to the CRM exchange via Celery/RabbitMQ.
Task names follow the ``<exchange>.record_watcher.<action>`` naming
convention used by other producers in the system.  Events are sent
after successful database transactions within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.record_watcher_event import (
    RecordWatcherCreatedEvent,
    RecordWatcherDeletedEvent,
)
from .common import BaseProducer


class RecordWatcherMessageProducer(BaseProducer):
    """Publishes record watcher lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.record_watcher.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.record_watcher.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_watcher_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a record_watcher.created event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owns the watcher.
        payload : dict
            Snapshot of the created watcher.
        """
        message = RecordWatcherCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_watcher_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a record_watcher.deleted event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owned the watcher.
        deleted_dt : str | None
            ISO 8601 timestamp indicating when the deletion occurred.  If
            omitted, consumers may use the message processing timestamp.
        """
        message = RecordWatcherDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


# Backwards compatibility alias
RecordWatcherProducer = RecordWatcherMessageProducer
