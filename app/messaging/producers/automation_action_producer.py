"""
Automation action event producer for the CRM service.

This module defines a message producer class that publishes
automation action lifecycle events to the CRM exchange via Celery/RabbitMQ.
Task names follow the ``<exchange>.automation_action.<action>`` naming
convention.  Producers send events after successful database
transactions within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.automation_action_event import (
    AutomationActionCreatedEvent,
    AutomationActionUpdatedEvent,
    AutomationActionDeletedEvent,
)
from .common import BaseProducer


class AutomationActionMessageProducer(BaseProducer):
    """Publishes automation action lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.automation_action.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.automation_action.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.automation_action.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_action_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish an automation_action.created event."""
        message = AutomationActionCreatedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_action_updated(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish an automation_action.updated event."""
        message = AutomationActionUpdatedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_action_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish an automation_action.deleted event."""
        message = AutomationActionDeletedEvent(tenant_id=tenant_id, deleted_dt=deleted_dt)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


# Backwards compatibility alias
AutomationActionProducer = AutomationActionMessageProducer
