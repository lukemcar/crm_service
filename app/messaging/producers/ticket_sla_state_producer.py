"""
Producer for ticket SLA state events.

This module encapsulates the publishing logic for ticket SLA state
events.  Currently only ``ticket_sla_state.updated`` events are
supported, triggered when SLA deadlines or breach flags are recomputed
by the orchestration layer.  The task name follows the
``<exchange>.ticket_sla_state.updated`` convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_sla_state_event import (
    TicketSlaStateUpdatedEvent,
    TicketSlaStateDelta,
)
from .common import BaseProducer


class TicketSlaStateMessageProducer(BaseProducer):
    """Publishes ticket SLA state events via Celery/RabbitMQ."""

    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_sla_state.updated"

    @staticmethod
    def _build_headers(*, tenant_id: UUID, ticket_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
        }

    @classmethod
    def send_ticket_sla_state_updated(
        cls,
        *,
        tenant_id: UUID,
        ticket_id: UUID,
        changes: TicketSlaStateDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_sla_state.updated event."""
        message = TicketSlaStateUpdatedEvent(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id, ticket_id=ticket_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)


__all__ = [
    "TicketSlaStateMessageProducer",
]
