"""
Producer for ticket assignment events.

This module encapsulates the logic for publishing ticket assignment
creation events to the message broker.  Task names follow the
``<exchange>.ticket_assignment.<action>`` convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_assignment_event import (
    TicketAssignmentCreatedEvent,
)
from .common import BaseProducer


class TicketAssignmentMessageProducer(BaseProducer):
    """Publishes ticket assignment lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_assignment.created"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_assignment_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_assignment.created event."""
        message = TicketAssignmentCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)


__all__ = [
    "TicketAssignmentMessageProducer",
]