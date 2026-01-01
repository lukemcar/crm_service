"""
Producer for ticket metrics lifecycle events.

This module encapsulates the publishing logic for ticket metrics
events.  Task names follow the ``<exchange>.ticket_metrics.<action>``
convention consistent with other support domain producers.  Events
are published after successful database mutations within the service
layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.ticket_metrics_event import (
    TicketMetricsCreatedEvent,
    TicketMetricsUpdatedEvent,
    TicketMetricsDeletedEvent,
    TicketMetricsDelta,
)
from .common import BaseProducer


class TicketMetricsMessageProducer(BaseProducer):
    """Publishes ticket metrics lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.ticket_metrics.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.ticket_metrics.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.ticket_metrics.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_ticket_metrics_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_metrics.created event."""
        message = TicketMetricsCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_metrics_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: TicketMetricsDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ticket_metrics.updated event."""
        message = TicketMetricsUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_ticket_metrics_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ticket_metrics.deleted event."""
        message = TicketMetricsDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["TicketMetricsMessageProducer"]