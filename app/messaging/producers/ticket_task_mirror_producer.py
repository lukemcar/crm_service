"""
Producer for ticket task mirror events.

This module encapsulates the logic for publishing ticket task mirror
lifecycle events to the message broker. Task names follow the
``<exchange>.ticket_task_mirror.<action>`` convention. Consumers can
subscribe to these tasks to update downstream systems when task
mirrors are created, updated or deleted.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_task_mirror_event import (
    TicketTaskMirrorCreatedEvent,
    TicketTaskMirrorUpdatedEvent,
    TicketTaskMirrorDeletedEvent,
    TicketTaskMirrorDelta,
)
from .common import BaseProducer


class TicketTaskMirrorMessageProducer(BaseProducer):
    """Publishes ticket task mirror lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_task_mirror.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_task_mirror.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_task_mirror.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_task_mirror_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_task_mirror.created event."""
        message = TicketTaskMirrorCreatedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_task_mirror_updated(
        cls,
        *,
        tenant_id: UUID,
        delta: TicketTaskMirrorDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_task_mirror.updated event."""
        message = TicketTaskMirrorUpdatedEvent(
            tenant_id=tenant_id, delta=delta, payload=payload
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_task_mirror_deleted(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_task_mirror.deleted event."""
        message = TicketTaskMirrorDeletedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "TicketTaskMirrorMessageProducer",
]