"""Producer for ticket time entry lifecycle events.

This module encapsulates the publishing logic for ticket time entry
events. Task names follow the ``<exchange>.ticket_time_entry.<action>``
convention consistent with other support domain producers. Events are
published after successful database mutations within the service
layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_time_entry_event import (
    TicketTimeEntryCreatedEvent,
    TicketTimeEntryUpdatedEvent,
    TicketTimeEntryDeletedEvent,
    TicketTimeEntryDelta,
)
from .common import BaseProducer


class TicketTimeEntryMessageProducer(BaseProducer):
    """Publishes ticket time entry lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_time_entry.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_time_entry.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_time_entry.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_time_entry_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_time_entry.created event."""
        message = TicketTimeEntryCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_time_entry_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: TicketTimeEntryDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_time_entry.updated event."""
        message = TicketTimeEntryUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_time_entry_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ticket_time_entry.deleted event."""
        message = TicketTimeEntryDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["TicketTimeEntryMessageProducer"]