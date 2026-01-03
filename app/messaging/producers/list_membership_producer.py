"""
List membership event producer for the CRM service.

This module defines a message producer class that publishes list
membership lifecycle events to the CRM exchange via Celery.  Memberships
associate individual records with lists; creations and deletions are
propagated to downstream services via these events.  The fully
qualified task names derive from the global exchange name (e.g.
``crm.list_membership.created``).  Messages are wrapped in Pydantic
models to ensure consistent schemas across producers and consumers.

``ListMembershipMessageProducer`` should be used by the service layer
(``list_membership_service.py``) to emit events after a successful
database commit.  Consumers can rely on these messages being sent
exactly once after the transaction has been committed.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.list_membership_event import (
    ListMembershipCreatedMessage,
    ListMembershipDeletedMessage,
)
from .common import BaseProducer


class ListMembershipMessageProducer(BaseProducer):
    """Publishes list membership lifecycle events via Celery.

    Task names are derived from the global ``EXCHANGE_NAME`` so that list
    membership events share the same exchange as other CRM entities.  Each
    event includes headers containing the tenant ID to aid in routing and
    filtering.  Clients should always prefer these ``send_*`` methods for
    publishing events.
    """

    TASK_CREATED: str = f"{EXCHANGE_NAME}.list_membership.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.list_membership.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_membership_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a list_membership.created event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owns the list membership.
        payload : dict
            Snapshot of the created membership.
        """
        message = ListMembershipCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_membership_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a list_membership.deleted event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owned the list membership.
        deleted_dt : str | None
            ISO 8601 timestamp indicating when the deletion occurred.  If
            omitted, consumers may use the message processing timestamp.
        """
        message = ListMembershipDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


# Backwards compatibility alias
ListMembershipProducer = ListMembershipMessageProducer
