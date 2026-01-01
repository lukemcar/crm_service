"""
Producer for ticket form field lifecycle events.

This module encapsulates the publishing logic for ticket form field
events.  Task names follow the ``<exchange>.ticket_form_field.<action>``
convention consistent with other domain producers.  Events are
published after successful database mutations within the service
layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_form_field_event import (
    TicketFormFieldCreatedEvent,
    TicketFormFieldUpdatedEvent,
    TicketFormFieldDeletedEvent,
    TicketFormFieldDelta,
)
from .common import BaseProducer


class TicketFormFieldMessageProducer(BaseProducer):
    """Publishes ticket form field lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_form_field.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_form_field.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_form_field.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_form_field_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_form_field.created event."""
        message = TicketFormFieldCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_form_field_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: TicketFormFieldDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_form_field.updated event."""
        message = TicketFormFieldUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_form_field_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ticket_form_field.deleted event."""
        message = TicketFormFieldDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "TicketFormFieldMessageProducer",
]