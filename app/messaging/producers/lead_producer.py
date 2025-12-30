"""
Producer for lead lifecycle events.

This module encapsulates the logic for publishing lead created,
updated and deleted events via Celery/RabbitMQ.  Task names follow
the ``<exchange>.lead.<action>`` pattern to align with the existing
group event naming convention.  Messages are wrapped in Pydantic
models to ensure type safety and consistency.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.lead_events import (
    LeadCreatedMessage,
    LeadUpdatedMessage,
    LeadDeletedMessage,
)
from .common import BaseProducer


class LeadMessageProducer(BaseProducer):
    """Publishes lead lifecycle events via Celery."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.lead.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.lead.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.lead.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        """Construct message headers to include the tenant identifier."""
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_lead_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a lead.created event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owns the lead.
        payload: dict
            Snapshot of the created lead.
        """
        message = LeadCreatedMessage(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_lead_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a lead.updated event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owns the lead.
        changes: dict
            Subset of lead attributes that have changed.
        payload: dict
            Full snapshot of the updated lead.
        """
        message = LeadUpdatedMessage(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_lead_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a lead.deleted event.

        Parameters
        ----------
        tenant_id: UUID
            Identifier of the tenant that owned the lead.
        deleted_dt: str | None
            ISO 8601 timestamp indicating when the deletion occurred.  If
            omitted, consumers may use the message processing timestamp.
        """
        message = LeadDeletedMessage(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
