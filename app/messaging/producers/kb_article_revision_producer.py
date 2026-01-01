"""
Producer for knowledge base article revision events.

Publishes events for creation and deletion of article revisions via Celery.
Task names follow the ``<exchange>.kb_article_revision.<action>`` pattern.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.kb_article_revision_event import (
    KbArticleRevisionCreatedEvent,
    KbArticleRevisionDeletedEvent,
)
from .common import BaseProducer


class KbArticleRevisionMessageProducer(BaseProducer):
    """Publishes knowledge base article revision events via Celery."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.kb_article_revision.created"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.kb_article_revision.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_kb_article_revision_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = KbArticleRevisionCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_article_revision_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = KbArticleRevisionDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["KbArticleRevisionMessageProducer"]