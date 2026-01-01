"""
Producer for knowledge base article lifecycle events.

Publishes events for CRUD operations on knowledge base articles via Celery.
Task names follow the ``<exchange>.kb_article.<action>`` convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.kb_article_event import (
    KbArticleCreatedEvent,
    KbArticleUpdatedEvent,
    KbArticleDeletedEvent,
    KbArticleDelta,
)
from .common import BaseProducer


class KbArticleMessageProducer(BaseProducer):
    """Publishes knowledge base article lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.kb_article.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.kb_article.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.kb_article.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_kb_article_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = KbArticleCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_article_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: KbArticleDelta,
        payload: Dict[str, Any],
    ) -> None:
        message = KbArticleUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_kb_article_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = KbArticleDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["KbArticleMessageProducer"]