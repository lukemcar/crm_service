"""
Producer for company‑to‑company relationship events.

This module provides a dedicated publisher for events related to
relationships between companies.  Relationship events are emitted
separately from company update events to allow downstream services
to handle them independently.  Task names follow the pattern
``<exchange>.company_relationship.<action>``.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.company_relationship_events import (
    CompanyRelationshipCreatedEvent,
    CompanyRelationshipUpdatedEvent,
    CompanyRelationshipDeletedEvent,
)
from .common import BaseProducer


class CompanyRelationshipMessageProducer(BaseProducer):
    """Publishes events for company‑to‑company relationship lifecycle."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.company_relationship.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.company_relationship.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.company_relationship.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID) -> Dict[str, str]:
        return {
            "tenant_id": str(tenant_id),
        }

    @classmethod
    def send_relationship_created(
        cls,
        *,
        tenant_id: UUID,
        from_company_id: UUID,
        to_company_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = CompanyRelationshipCreatedEvent(
            tenant_id=tenant_id,
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_relationship_updated(
        cls,
        *,
        tenant_id: UUID,
        from_company_id: UUID,
        to_company_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = CompanyRelationshipUpdatedEvent(
            tenant_id=tenant_id,
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_relationship_deleted(
        cls,
        *,
        tenant_id: UUID,
        from_company_id: UUID,
        to_company_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = CompanyRelationshipDeletedEvent(
            tenant_id=tenant_id,
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
