"""
Producer for knowledge base article feedback events.

Publishes events for creation and deletion of article feedback via Celery.
Task names follow the ``<exchange>.kb_article_feedback.<action>`` pattern.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.kb_article_feedback_event import (
    KbArticleFeedbackCreatedEvent,
    KbArticleFeedbackDeletedEvent,
)
from .common import BaseProducer


class KbArticleFeedbackMessageProducer(BaseProducer):
    """Publishes knowledge base article feedback events via Celery."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.kb_article_feedback.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.kb_article_feedback.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_kb_article_feedback_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = KbArticleFeedbackCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_article_feedback_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = KbArticleFeedbackDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["KbArticleFeedbackMessageProducer"]