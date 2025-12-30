"""
Producer for contact lifecycle events.

This module encapsulates the publishing logic for contact events.
Task names follow the ``<exchange>.contact.<action>`` convention
consistent with the rest of the system.  Events are sent after
successful database transactions within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.contact_event import (
    ContactCreatedEvent,
    ContactUpdatedEvent,
    ContactDeletedEvent,
    ContactDelta,
)
from .common import BaseProducer


class ContactMessageProducer(BaseProducer):
    """Publishes contact lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.contact.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.contact.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.contact.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_contact_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a contact.created event."""
        message = ContactCreatedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_contact_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: ContactDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a contact.updated event."""
        message = ContactUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_contact_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a contact.deleted event."""
        message = ContactDeletedEvent(tenant_id=tenant_id, deleted_dt=deleted_dt)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
