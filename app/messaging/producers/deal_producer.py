"""
Deal event producer for the CRM service.

This module defines a message producer class that publishes deal
lifecycle events to the CRM exchange via Celery.  Each CRUD action
on a deal results in a message being sent with a fully qualified
task name (e.g. ``crm.deal.created``).  Messages are wrapped in
Pydantic models to ensure consistent schema across producers and
consumers.  Headers include the tenant ID to aid in routing and
filtering.

``DealMessageProducer`` should be used by the service layer
(``deal_service.py``) to emit events after a successful database
commit.  Consumers of deal events can rely on these messages
being sent exactly once after the transaction has been committed.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.deal_event import (
    DealCreatedMessage,
    DealUpdatedMessage,
    DealDeletedMessage,
)
from .common import BaseProducer


class DealMessageProducer(BaseProducer):
    """Publishes deal lifecycle events via Celery.

    Task names are derived from the global ``EXCHANGE_NAME`` so that
    deals share the same exchange as other CRM entities.  Each event
    includes headers containing the tenant ID to aid in routing and
    filtering.  Clients should always prefer these ``send_*`` methods
    for publishing events.
    """

    # Fully qualified task names following the pattern ``<exchange>.deal.<action>``
    TASK_CREATED: str = f"{EXCHANGE_NAME}.deal.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.deal.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.deal.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        """Construct message headers to include the tenant identifier."""
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_deal_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a deal.created event."""
        message = DealCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_deal_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a deal.updated event."""
        message = DealUpdatedMessage(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_deal_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a deal.deleted event."""
        message = DealDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)

# Backwards compatibility alias
DealProducer = DealMessageProducer
