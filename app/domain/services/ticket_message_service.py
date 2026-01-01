"""
Service layer for TicketMessage entities.

This module implements list and create operations for ticket
messages.  Messages are append-only; there is no update or delete
operation.  Service functions enforce tenant scoping and emit
appropriate events via the ticket message producer after
successful commits.  Unique and check constraints are enforced at
the database layer; violations will surface as integrity errors via
``commit_or_raise``.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status  # noqa: F401
from sqlalchemy.orm import Session

from app.domain.models.ticket_message import TicketMessage
from app.domain.schemas.ticket_message import (
    TenantCreateTicketMessage,
    AdminCreateTicketMessage,
)
from app.messaging.producers.ticket_message_producer import (
    TicketMessageMessageProducer as MessageProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_message_service")


def _snapshot(message):
    """Return a dictionary representation of a TicketMessage for event payloads.

    Note: the provider payload snapshot field was renamed from ``metadata`` to
    ``provider_metadata`` to avoid conflict with SQLAlchemy's reserved
    attribute.  The database column name remains "metadata", but all Python
    references use ``provider_metadata``.
    """
    return {
        "id": message.id,
        "tenant_id": message.tenant_id,
        "ticket_id": message.ticket_id,
        "author_type": message.author_type,
        "author_contact_id": message.author_contact_id,
        "author_user_id": message.author_user_id,
        "author_display_name": message.author_display_name,
        "is_public": message.is_public,
        "channel_type": message.channel_type,
        "external_ref": message.external_ref,
        "subject": message.subject,
        "body": message.body,
        # emit renamed field in event payload
        "provider_metadata": message.provider_metadata,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "created_by": message.created_by,
    }


def list_ticket_messages(
    db,
    *,
    tenant_id,
    ticket_id,
    author_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    channel_type: Optional[str] = None,
) -> List[TicketMessage]:
    """List ticket messages for a given ticket with optional filters."""
    logger.debug(
        "Listing ticket messages: tenant_id=%s, ticket_id=%s, author_type=%s, is_public=%s, channel_type=%s",
        tenant_id,
        ticket_id,
        author_type,
        is_public,
        channel_type,
    )
    query = db.query(TicketMessage).filter(
        TicketMessage.tenant_id == tenant_id,
        TicketMessage.ticket_id == ticket_id,
    )
    if author_type:
        query = query.filter(TicketMessage.author_type == author_type)
    if is_public is not None:
        query = query.filter(TicketMessage.is_public == is_public)
    if channel_type:
        query = query.filter(TicketMessage.channel_type == channel_type)
    return query.order_by(TicketMessage.created_at.asc()).all()


def create_ticket_message(
    db,
    *,
    tenant_id,
    ticket_id,
    request,
    created_by: str,
) -> TicketMessage:
    """Create a ticket message and publish a created event."""
    logger.debug(
        "Creating ticket message: tenant_id=%s, ticket_id=%s, author_type=%s",
        tenant_id,
        ticket_id,
        request.author_type,
    )
    message = TicketMessage(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        author_type=request.author_type,
        author_contact_id=request.author_contact_id,
        author_user_id=request.author_user_id,
        author_display_name=request.author_display_name,
        is_public=request.is_public,
        channel_type=request.channel_type,
        external_ref=request.external_ref,
        subject=request.subject,
        body=request.body,
        provider_metadata=request.provider_metadata,
        created_by=created_by,
    )
    db.add(message)
    commit_or_raise(db, refresh=message, action="create ticket message")
    snapshot = _snapshot(message)
    MessageProducer.send_ticket_message_created(tenant_id=tenant_id, payload=snapshot)
    return message