"""
Producer for ticket AI work reference events.

This module encapsulates the logic for publishing ticket AI work
reference lifecycle events to the message broker. Task names follow the
``<exchange>.ticket_ai_work_ref.<action>`` convention. These events
inform downstream systems when AI work references are created, updated
or deleted.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_ai_work_ref_event import (
    TicketAiWorkRefCreatedEvent,
    TicketAiWorkRefUpdatedEvent,
    TicketAiWorkRefDeletedEvent,
    TicketAiWorkRefDelta,
)
from .common import BaseProducer


class TicketAiWorkRefMessageProducer(BaseProducer):
    """Publishes ticket AI work reference lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_ai_work_ref.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_ai_work_ref.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_ai_work_ref.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_ai_work_ref_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_ai_work_ref.created event."""
        message = TicketAiWorkRefCreatedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_ai_work_ref_updated(
        cls,
        *,
        tenant_id: UUID,
        delta: TicketAiWorkRefDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_ai_work_ref.updated event."""
        message = TicketAiWorkRefUpdatedEvent(
            tenant_id=tenant_id, delta=delta, payload=payload
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_ai_work_ref_deleted(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_ai_work_ref.deleted event."""
        message = TicketAiWorkRefDeletedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "TicketAiWorkRefMessageProducer",
]