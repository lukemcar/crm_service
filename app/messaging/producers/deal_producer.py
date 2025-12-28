"""
Producer for deal lifecycle events.

Publishes events when deals are created, updated or deleted.  These
events allow downstream services to stay in sync with changes to
revenue opportunities.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    DealCreatedMessage,
    DealUpdatedMessage,
    DealDeletedMessage,
)
from .common import BaseProducer


class DealProducer(BaseProducer):
    """Producer for deal events."""

    @classmethod
    def publish_deal_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = DealCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.deal.created", message_model=message)

    @classmethod
    def publish_deal_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = DealUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.deal.updated", message_model=message)

    @classmethod
    def publish_deal_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = DealDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.deal.deleted", message_model=message)
