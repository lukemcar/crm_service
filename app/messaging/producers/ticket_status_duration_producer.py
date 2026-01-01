"""
Producer for ticket status duration lifecycle events.

This module encapsulates the publishing logic for ticket status
duration events.  Task names follow the
``<exchange>.ticket_status_duration.<action>`` convention.  Events
are published after successful mutations within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_status_duration_event import (
    TicketStatusDurationCreatedEvent,
    TicketStatusDurationUpdatedEvent,
    TicketStatusDurationDeletedEvent,
    TicketStatusDurationDelta,
)
from .common import BaseProducer


class TicketStatusDurationMessageProducer(BaseProducer):
    """Publishes ticket status duration lifecycle events via Celery."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_status_duration.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_status_duration.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_status_duration.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_status_duration_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = TicketStatusDurationCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_status_duration_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: TicketStatusDurationDelta,
        payload: Dict[str, Any],
    ) -> None:
        message = TicketStatusDurationUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_status_duration_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = TicketStatusDurationDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["TicketStatusDurationMessageProducer"]