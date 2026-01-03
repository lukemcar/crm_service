"""
List event producer for the CRM service.

This module defines a message producer class that publishes list
lifecycle events to the CRM exchange via Celery.  Each CRUD action on a
list results in a message being sent with a fully qualified task name
derived from the global exchange name (e.g. ``crm.list.created``).  Messages
are wrapped in Pydantic models to ensure consistent schema across
producers and consumers.  Headers include the tenant ID to aid in
routing and filtering.

``ListMessageProducer`` should be used by the service layer
(``list_service.py``) to emit events after a successful database
commit.  Consumers of list events can rely on these messages being
sent exactly once after the transaction has been committed.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.list_event import (
    ListCreatedMessage,
    ListUpdatedMessage,
    ListDeletedMessage,
)
from .common import BaseProducer


class ListMessageProducer(BaseProducer):
    """Publishes list lifecycle events via Celery.

    Task names are derived from the global ``EXCHANGE_NAME`` so that
    lists share the same exchange as other CRM entities.  Each event
    includes headers containing the tenant ID to aid in routing and
    filtering.  Clients should always prefer these ``send_*`` methods
    for publishing events.
    """

    # Fully qualified task names following the pattern ``<exchange>.list.<action>``
    TASK_CREATED: str = f"{EXCHANGE_NAME}.list.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.list.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.list.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        """Construct message headers to include the tenant identifier."""
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_list_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a list.created event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owns the list.
        payload: dict
            Snapshot of the created list.
        """
        message = ListCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_list_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a list.updated event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owns the list.
        changes: dict
            Subset of list attributes that have changed.
        payload: dict
            Full snapshot of the updated list.
        """
        message = ListUpdatedMessage(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_list_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a list.deleted event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owned the list.
        deleted_dt: str | None
            ISO 8601 timestamp indicating when the deletion occurred.  If
            omitted, consumers may use the message processing timestamp.
        """
        message = ListDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


# Backwards compatibility alias.  Some parts of the codebase may still
# refer to ``ListProducer``.  Exporting this alias preserves those
# references without breaking imports.
ListProducer = ListMessageProducer
