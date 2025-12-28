"""
Producer for list lifecycle events.

Lists (segments) allow grouping records based on criteria.  These
producer methods emit events when lists are created, updated or
deleted so that other services can maintain their own segment
definitions.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    ListCreatedMessage,
    ListUpdatedMessage,
    ListDeletedMessage,
)
from .common import BaseProducer


class ListProducer(BaseProducer):
    """Producer for list events."""

    @classmethod
    def publish_list_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = ListCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.list.created", message_model=message)

    @classmethod
    def publish_list_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = ListUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.list.updated", message_model=message)

    @classmethod
    def publish_list_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = ListDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.list.deleted", message_model=message)
