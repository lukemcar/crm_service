"""
Producer for company lifecycle events.

This module encapsulates the publishing logic for company events.
Task names follow the ``<exchange>.company.<action>`` convention consistent
with the rest of the system.  Events are sent after successful
database transactions within the service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from company_events import (
    CompanyCreatedEvent,
    CompanyUpdatedEvent,
    CompanyDeletedEvent,
    CompanyDelta,
)
from .common import BaseProducer


class CompanyMessageProducer(BaseProducer):
    """Publishes company lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.company.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.company.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.company.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_company_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a company.created event."""
        message = CompanyCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_company_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: CompanyDelta,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a company.updated event."""
        message = CompanyUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_company_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a company.deleted event."""
        message = CompanyDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
