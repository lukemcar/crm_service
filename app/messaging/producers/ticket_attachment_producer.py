"""
Producer for ticket attachment events.

This module encapsulates the logic for publishing ticket attachment
creation and deletion events to the message broker.  Task names
follow the ``<exchange>.ticket_attachment.<action>`` convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_attachment_event import (
    TicketAttachmentCreatedEvent,
    TicketAttachmentDeletedEvent,
)
from .common import BaseProducer


class TicketAttachmentMessageProducer(BaseProducer):
    """Publishes ticket attachment lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_attachment.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_attachment.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_attachment_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_attachment.created event."""
        message = TicketAttachmentCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_attachment_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ticket_attachment.deleted event."""
        message = TicketAttachmentDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "TicketAttachmentMessageProducer",
]