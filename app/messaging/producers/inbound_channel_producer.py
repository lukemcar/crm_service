"""
Producer for inbound channel lifecycle events.

This module encapsulates the publishing logic for inbound channel
events.  Task names follow the ``<exchange>.inbound_channel.<action>``
convention consistent with other domain producers.  Events are
published after successful database mutations within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.inbound_channel_event import (
    InboundChannelCreatedEvent,
    InboundChannelUpdatedEvent,
    InboundChannelDeletedEvent,
    InboundChannelDelta,
)
from .common import BaseProducer


class InboundChannelMessageProducer(BaseProducer):
    """Publishes inbound channel lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.inbound_channel.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.inbound_channel.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.inbound_channel.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_inbound_channel_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish an inbound_channel.created event."""
        message = InboundChannelCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_inbound_channel_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: InboundChannelDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish an inbound_channel.updated event."""
        message = InboundChannelUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_inbound_channel_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish an inbound_channel.deleted event."""
        message = InboundChannelDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "InboundChannelMessageProducer",
]