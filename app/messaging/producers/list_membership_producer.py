"""
Producer for list membership events.

List memberships associate records with lists.  When a membership
is created or deleted, these producer methods emit events to keep
other services in sync with segment membership changes.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    ListMembershipCreatedMessage,
    ListMembershipDeletedMessage,
)
from .common import BaseProducer


class ListMembershipProducer(BaseProducer):
    """Producer for list membership events."""

    @classmethod
    def publish_membership_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = ListMembershipCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.list_membership.created", message_model=message)

    @classmethod
    def publish_membership_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = ListMembershipDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.list_membership.deleted", message_model=message)
