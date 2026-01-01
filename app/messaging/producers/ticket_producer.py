"""
Producer for ticket lifecycle events.

This module encapsulates the publishing logic for ticket events.
Task names follow the ``<exchange>.ticket.<action>`` convention
consistent with other domain producers.  Events are published after
successful database operations in the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_event import (
    TicketCreatedEvent,
    TicketUpdatedEvent,
    TicketDeletedEvent,
    TicketDelta,
)
from .common import BaseProducer


class TicketMessageProducer(BaseProducer):
    """Publishes ticket lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket.created event."""
        message = TicketCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: TicketDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket.updated event."""
        message = TicketUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ticket.deleted event."""
        message = TicketDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "TicketMessageProducer",
]