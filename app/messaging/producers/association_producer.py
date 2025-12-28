"""
Producer for association events.

Associations link records of different types (e.g., contact to company).
These producer methods emit events when associations are created or
deleted so that other services can update their own relationship
mappings.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    AssociationCreatedMessage,
    AssociationDeletedMessage,
)
from .common import BaseProducer


class AssociationProducer(BaseProducer):
    """Producer for association events."""

    @classmethod
    def publish_association_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = AssociationCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.association.created", message_model=message)

    @classmethod
    def publish_association_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = AssociationDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.association.deleted", message_model=message)
