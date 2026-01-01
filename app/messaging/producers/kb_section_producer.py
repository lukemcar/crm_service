"""
Producer for knowledge base section lifecycle events.

Publishes events for CRUD operations on knowledge base sections via Celery.
Task names follow the ``<exchange>.kb_section.<action>`` convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.kb_section_event import (
    KbSectionCreatedEvent,
    KbSectionUpdatedEvent,
    KbSectionDeletedEvent,
    KbSectionDelta,
)
from .common import BaseProducer


class KbSectionMessageProducer(BaseProducer):
    """Publishes knowledge base section lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.kb_section.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.kb_section.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.kb_section.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_kb_section_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = KbSectionCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_section_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: KbSectionDelta,
        payload: Dict[str, Any],
    ) -> None:
        message = KbSectionUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_section_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = KbSectionDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["KbSectionMessageProducer"]