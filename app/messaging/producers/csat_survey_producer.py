"""Producer for CSAT survey lifecycle events.

This module encapsulates the publishing logic for CSAT survey events.
Task names follow the ``<exchange>.csat_survey.<action>`` convention.
Events are published after successful database mutations within the
service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.csat_survey_event import (
    CsatSurveyCreatedEvent,
    CsatSurveyUpdatedEvent,
    CsatSurveyDeletedEvent,
    CsatSurveyDelta,
)
from .common import BaseProducer


class CsatSurveyMessageProducer(BaseProducer):
    """Publishes CSAT survey lifecycle events via Celery/RabbitMQ."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.csat_survey.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.csat_survey.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.csat_survey.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_csat_survey_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = CsatSurveyCreatedEvent(
            tenant_id=tenant_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_csat_survey_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: CsatSurveyDelta,
        payload: Dict[str, Any],
    ) -> None:
        message = CsatSurveyUpdatedEvent(
            tenant_id=tenant_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_csat_survey_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = CsatSurveyDeletedEvent(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["CsatSurveyMessageProducer"]