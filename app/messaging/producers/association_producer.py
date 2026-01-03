"""
Association event producer for the CRM service.

This module defines a message producer class that publishes association
lifecycle events to the CRM exchange via Celery.  Associations link
records of different types and are immutable; clients should delete
and recreate associations instead of updating them.  Therefore, only
``created`` and ``deleted`` events are emitted.  Messages are wrapped
in Pydantic models to ensure consistent schema across producers and
consumers.  Headers include the tenant ID to aid in routing and
filtering.

``AssociationMessageProducer`` should be used by the service layer
(``association_service.py``) to emit events after a successful database
commit.  Consumers of association events can rely on these messages
being sent exactly once after the transaction has been committed.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.association_event import (
    AssociationCreatedMessage,
    AssociationDeletedMessage,
)
from .common import BaseProducer


class AssociationMessageProducer(BaseProducer):
    """Publishes association lifecycle events via Celery.

    Associations are immutable; only create and delete events are published.
    Task names are derived from the global ``EXCHANGE_NAME`` so that
    associations share the same exchange as other CRM entities.  Each event
    includes headers containing the tenant ID to aid in routing and
    filtering.
    """

    # Fully qualified task names following the pattern ``<exchange>.association.<action>``
    TASK_CREATED: str = f"{EXCHANGE_NAME}.association.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.association.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        """Construct message headers to include the tenant identifier."""
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_association_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish an association.created event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owns the association.
        payload: dict
            Snapshot of the created association.
        """
        message = AssociationCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_association_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish an association.deleted event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owned the association.
        deleted_dt: str | None
            ISO 8601 timestamp indicating when the deletion occurred.  If
            omitted, consumers may use the message processing timestamp.
        """
        message = AssociationDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)