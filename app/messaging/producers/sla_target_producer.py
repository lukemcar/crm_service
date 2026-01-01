"""
Producer for SLA target lifecycle events.

This module encapsulates the publishing logic for SLA target events.
Task names follow the ``<exchange>.sla_target.<action>`` convention
consistent with other domain producers.  Events are published after
successful database mutations within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.sla_target_event import (
    SlaTargetCreatedEvent,
    SlaTargetUpdatedEvent,
    SlaTargetDeletedEvent,
    SlaTargetDelta,
)
from .common import BaseProducer


class SlaTargetMessageProducer(BaseProducer):
    """Publishes SLA target lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.sla_target.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.sla_target.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.sla_target.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_sla_target_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a sla_target.created event."""
        message = SlaTargetCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_sla_target_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: SlaTargetDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a sla_target.updated event."""
        message = SlaTargetUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_sla_target_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a sla_target.deleted event."""
        message = SlaTargetDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "SlaTargetMessageProducer",
]
