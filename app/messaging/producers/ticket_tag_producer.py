"""
Producer for ticket tag events.

This module encapsulates the logic for publishing ticket tag
creation and deletion events to the message broker.  Task names
follow the ``<exchange>.ticket_tag.<action>`` convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_tag_event import (
    TicketTagCreatedEvent,
    TicketTagDeletedEvent,
)
from .common import BaseProducer


class TicketTagMessageProducer(BaseProducer):
    """Publishes ticket tag lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_tag.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_tag.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_tag_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_tag.created event."""
        message = TicketTagCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_tag_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ticket_tag.deleted event."""
        message = TicketTagDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "TicketTagMessageProducer",
]