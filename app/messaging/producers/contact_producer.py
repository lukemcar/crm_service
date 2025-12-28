"""
Producer for contact lifecycle events.

This module provides helper methods to publish contact lifecycle
events.  Each method constructs the appropriate message model and
invokes the ``BaseProducer`` to wrap and emit the event.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    ContactCreatedMessage,
    ContactUpdatedMessage,
    ContactDeletedMessage,
)
from .common import BaseProducer


class ContactProducer(BaseProducer):
    """Producer for contact events."""

    @classmethod
    def publish_contact_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ContactCreated event."""
        message = ContactCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.contact.created", message_model=message)

    @classmethod
    def publish_contact_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ContactUpdated event."""
        message = ContactUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.contact.updated", message_model=message)

    @classmethod
    def publish_contact_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ContactDeleted event."""
        message = ContactDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.contact.deleted", message_model=message)
