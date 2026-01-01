"""
Producer for group profile lifecycle events.

This module encapsulates the publishing logic for group profile events.
Task names follow the ``<exchange>.group_profile.<action>`` convention
consistent with the rest of the system.  Events are sent after
successful database transactions within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.group_profile_event import (
    GroupProfileCreatedEvent,
    GroupProfileUpdatedEvent,
    GroupProfileDeletedEvent,
    GroupProfileDelta,
)
from .common import BaseProducer


class GroupProfileMessageProducer(BaseProducer):
    """Publishes group profile lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.group_profile.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.group_profile.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.group_profile.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_group_profile_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a group_profile.created event."""
        message = GroupProfileCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_group_profile_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: GroupProfileDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a group_profile.updated event."""
        message = GroupProfileUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_group_profile_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a group_profile.deleted event."""
        message = GroupProfileDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = [
    "GroupProfileMessageProducer",
]
