"""
Producer for activity lifecycle events.

Activities include notes, calls, tasks and other time‑line records.
Publishing these events keeps other systems (e.g. analytics or
notifications) aware of changes in activity data.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    ActivityCreatedMessage,
    ActivityUpdatedMessage,
    ActivityDeletedMessage,
)
from .common import BaseProducer


class ActivityProducer(BaseProducer):
    """Producer for activity events."""

    @classmethod
    def publish_activity_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = ActivityCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.activity.created", message_model=message)

    @classmethod
    def publish_activity_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = ActivityUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.activity.updated", message_model=message)

    @classmethod
    def publish_activity_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = ActivityDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.activity.deleted", message_model=message)
