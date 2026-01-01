"""Producer for CSAT response lifecycle events.

This module handles the publishing of CSAT response events. Task names
follow the ``<exchange>.csat_response.<action>`` convention. Events are
published by services after successful mutations.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.csat_response_event import (
    CsatResponseCreatedEvent,
    CsatResponseUpdatedEvent,
    CsatResponseDeletedEvent,
    CsatResponseDelta,
)
from .common import BaseProducer


class CsatResponseMessageProducer(BaseProducer):
    """Publishes CSAT response lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.csat_response.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.csat_response.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.csat_response.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_csat_response_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = CsatResponseCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_csat_response_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: CsatResponseDelta,
        payload: Dict[str, Any],
    ) -> None:
        message = CsatResponseUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_csat_response_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = CsatResponseDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["CsatResponseMessageProducer"]