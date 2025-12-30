"""
Producer for contact‑company relationship events.

This module provides a dedicated publisher for events related to
contact/company relationships.  Relationship events are emitted
separately from contact update events to allow downstream services to
handle them independently.  Task names follow the pattern
``<exchange>.contact_company_relationship.<action>``.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from contact_company_relationship_events import (
    ContactCompanyRelationshipCreatedEvent,
    ContactCompanyRelationshipUpdatedEvent,
    ContactCompanyRelationshipDeletedEvent,
)
from tenant_group_producer import BaseProducer  # reuse base producer


class ContactCompanyRelationshipMessageProducer(BaseProducer):
    """Publishes events for contact‑company relationship lifecycle."""

    TASK_CREATED: str = f"{EXCHANGE_NAME}.contact_company_relationship.created"
    TASK_UPDATED: str = f"{EXCHANGE_NAME}.contact_company_relationship.updated"
    TASK_DELETED: str = f"{EXCHANGE_NAME}.contact_company_relationship.deleted"

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
        contact_id: UUID,
        company_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = ContactCompanyRelationshipCreatedEvent(
            tenant_id=tenant_id,
            contact_id=contact_id,
            company_id=company_id,
            payload=payload,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_relationship_updated(
        cls,
        *,
        tenant_id: UUID,
        contact_id: UUID,
        company_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = ContactCompanyRelationshipUpdatedEvent(
            tenant_id=tenant_id,
            contact_id=contact_id,
            company_id=company_id,
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
        contact_id: UUID,
        company_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        message = ContactCompanyRelationshipDeletedEvent(
            tenant_id=tenant_id,
            contact_id=contact_id,
            company_id=company_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(tenant_id=tenant_id)
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
