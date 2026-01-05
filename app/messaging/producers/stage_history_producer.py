"""
Producer for stage history events.

This module defines a message producer for stage history entries.  When a
stage transition occurs and a new ``StageHistory`` record is persisted,
the service layer should publish a ``stage_history.created`` event.  The
event carries a full snapshot of the stage history so that downstream
subscribers can update timelines or analytics.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.stage_history_event import StageHistoryCreatedEvent
from .common import BaseProducer


class StageHistoryMessageProducer(BaseProducer):
    """Publishes stage history events via Celery."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.stage_history.created"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_stage_history_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``stage_history.created`` event."""
        message = StageHistoryCreatedEvent(tenant_id=tenant_id, payload=payload)
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)


__all__ = ["StageHistoryMessageProducer"]