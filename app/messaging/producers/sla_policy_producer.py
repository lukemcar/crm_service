"""
Producer for SLA policy lifecycle events.

This module encapsulates the publishing logic for SLA policy events.
Task names follow the ``<exchange>.sla_policy.<action>`` convention
consistent with other domain producers.  Events are published after
successful database mutations within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.sla_policy_event import (
    SlaPolicyCreatedEvent,
    SlaPolicyUpdatedEvent,
    SlaPolicyDeletedEvent,
    SlaPolicyDelta,
)
from .common import BaseProducer


class SlaPolicyMessageProducer(BaseProducer):
    """Publishes SLA policy lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.sla_policy.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.sla_policy.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.sla_policy.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_sla_policy_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a sla_policy.created event."""
        message = SlaPolicyCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_sla_policy_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: SlaPolicyDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a sla_policy.updated event."""
        message = SlaPolicyUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_sla_policy_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a sla_policy.deleted event."""
        message = SlaPolicyDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "SlaPolicyMessageProducer",
]
