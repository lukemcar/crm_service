"""
Service layer for TicketTag entities.

This module implements list, create and delete operations for ticket
tags.  Tags are append‑only; there is no update operation.  Service
functions enforce tenant scoping and emit appropriate events via
the ticket tag producer after successful commits.  Unique
constraints are enforced at the database layer; violations will
surface as integrity errors via ``commit_or_raise``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_tag import TicketTag
from app.domain.schemas.ticket_tag import (
    TenantCreateTicketTag,
    AdminCreateTicketTag,
)
from app.messaging.producers.ticket_tag_producer import (
    TicketTagMessageProducer as TagProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_tag_service")


def _snapshot(tag: TicketTag) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketTag for event payloads."""
    return {
        "id": tag.id,
        "tenant_id": tag.tenant_id,
        "ticket_id": tag.ticket_id,
        "tag": tag.tag,
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
        "created_by": tag.created_by,
    }


def list_ticket_tags(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
) -> List[TicketTag]:
    """List tags for a given ticket."""
    logger.debug(
        "Listing ticket tags: tenant_id=%s, ticket_id=%s",
        tenant_id,
        ticket_id,
    )
    return (
        db.query(TicketTag)
        .filter(
            TicketTag.tenant_id == tenant_id,
            TicketTag.ticket_id == ticket_id,
        )
        .order_by(TicketTag.created_at.asc())
        .all()
    )


def create_ticket_tag(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateTicketTag | AdminCreateTicketTag,
    created_by: str,
) -> TicketTag:
    """Create a ticket tag and publish a created event."""
    logger.debug(
        "Creating ticket tag: tenant_id=%s, ticket_id=%s, tag=%s",
        tenant_id,
        ticket_id,
        request.tag,
    )
    tag = TicketTag(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        tag=request.tag,
        created_by=created_by,
    )
    db.add(tag)
    commit_or_raise(db, refresh=tag, action="create ticket tag")
    snapshot = _snapshot(tag)
    TagProducer.send_ticket_tag_created(tenant_id=tenant_id, payload=snapshot)
    return tag


def get_ticket_tag(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> TicketTag:
    """Retrieve a single ticket tag by ID within a tenant and ticket context."""
    tag = (
        db.query(TicketTag)
        .filter(
            TicketTag.id == tag_id,
            TicketTag.tenant_id == tenant_id,
            TicketTag.ticket_id == ticket_id,
        )
        .first()
    )
    if not tag:
        logger.info(
            "Ticket tag not found: tenant_id=%s, ticket_id=%s, tag_id=%s",
            tenant_id,
            ticket_id,
            tag_id,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket tag not found")
    return tag


def delete_ticket_tag(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> None:
    """Delete a ticket tag and publish a deletion event."""
    tag = get_ticket_tag(db, tenant_id=tenant_id, ticket_id=ticket_id, tag_id=tag_id)
    db.delete(tag)
    commit_or_raise(db, action="delete ticket tag")
    TagProducer.send_ticket_tag_deleted(
        tenant_id=tenant_id,
        deleted_dt=datetime.utcnow().isoformat(),
    )
    return None