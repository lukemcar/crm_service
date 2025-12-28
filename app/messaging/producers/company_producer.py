"""
Producer for company lifecycle events.

Provides helper methods to publish company created, updated and
deleted events.  Utilises the common ``BaseProducer`` to wrap
messages in an ``EventEnvelope`` and emit them.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.domain.schemas.events import (
    CompanyCreatedMessage,
    CompanyUpdatedMessage,
    CompanyDeletedMessage,
)
from .common import BaseProducer


class CompanyProducer(BaseProducer):
    """Producer for company events."""

    @classmethod
    def publish_company_created(
        cls,
        *,
        tenant_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = CompanyCreatedMessage(tenant_id=tenant_id, payload=payload)
        cls._send(task_name="crm.company.created", message_model=message)

    @classmethod
    def publish_company_updated(
        cls,
        *,
        tenant_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = CompanyUpdatedMessage(
            tenant_id=tenant_id, changes=changes, payload=payload
        )
        cls._send(task_name="crm.company.updated", message_model=message)

    @classmethod
    def publish_company_deleted(
        cls,
        *,
        tenant_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = CompanyDeletedMessage(tenant_id=tenant_id, deleted_dt=deleted_dt)
        cls._send(task_name="crm.company.deleted", message_model=message)
