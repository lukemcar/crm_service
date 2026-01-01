"""
Service layer for TicketAttachment entities.

This module implements list, create and delete operations for
ticket attachments.  Attachments are append-only; there is no
update operation.  Service functions enforce tenant scoping and
emit appropriate events via the ticket attachment producer after
successful commits.  Unique constraints are enforced at the
database layer; violations will surface as integrity errors via
``commit_or_raise``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import HTTPException, status  # noqa: F401
from sqlalchemy.orm import Session

from app.domain.models.ticket_attachment import TicketAttachment
from app.domain.schemas.ticket_attachment import (
    TenantCreateTicketAttachment,
    AdminCreateTicketAttachment,
)
from app.messaging.producers.ticket_attachment_producer import (
    TicketAttachmentMessageProducer as AttachmentProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_attachment_service")


def _snapshot(attachment):
    """Return a dictionary representation of a TicketAttachment for event payloads."""
    return {
        "id": attachment.id,
        "tenant_id": attachment.tenant_id,
        "ticket_id": attachment.ticket_id,
        "ticket_message_id": attachment.ticket_message_id,
        "file_name": attachment.file_name,
        "content_type": attachment.content_type,
        "file_size_bytes": attachment.file_size_bytes,
        "storage_provider": attachment.storage_provider,
        "storage_key": attachment.storage_key,
        "checksum_sha256": attachment.checksum_sha256,
        "created_at": attachment.created_at.isoformat() if attachment.created_at else None,
        "created_by": attachment.created_by,
    }

from typing import Optional


def list_ticket_attachments(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    ticket_message_id: Optional[uuid.UUID] = None,
    storage_provider: Optional[str] = None,
) -> List[TicketAttachment]:
    """List ticket attachments for a given ticket with optional filters.

    Attachments are scoped to a tenant and ticket.  Optionally filter by the
    associated ticket message or storage provider.
    """
    logger.debug(
        "Listing ticket attachments: tenant_id=%s, ticket_id=%s, ticket_message_id=%s, storage_provider=%s",
        tenant_id,
        ticket_id,
        ticket_message_id,
        storage_provider,
    )
    query = db.query(TicketAttachment).filter(
        TicketAttachment.tenant_id == tenant_id,
        TicketAttachment.ticket_id == ticket_id,
    )
    if ticket_message_id:
        query = query.filter(TicketAttachment.ticket_message_id == ticket_message_id)
    if storage_provider:
        query = query.filter(TicketAttachment.storage_provider == storage_provider)
    return query.order_by(TicketAttachment.created_at.asc()).all()


def create_ticket_attachment(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateTicketAttachment | AdminCreateTicketAttachment,
    created_by: str,
) -> TicketAttachment:
    """Create a ticket attachment and publish a created event.

    The request model differs slightly between tenant and admin contexts but
    shares the same fields for the attachment metadata.  The tenant_id
    parameter is taken from the path for tenant routes or from the request
    object for admin routes.
    """
    logger.debug(
        "Creating ticket attachment: tenant_id=%s, ticket_id=%s, file_name=%s",
        tenant_id,
        ticket_id,
        request.file_name,
    )
    attachment = TicketAttachment(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_message_id=getattr(request, "ticket_message_id", None),
        file_name=request.file_name,
        content_type=request.content_type,
        file_size_bytes=request.file_size_bytes,
        storage_provider=request.storage_provider,
        storage_key=request.storage_key,
        checksum_sha256=request.checksum_sha256,
        created_by=created_by,
    )
    db.add(attachment)
    # Commit and refresh to get assigned id and timestamps
    commit_or_raise(db, refresh=attachment, action="create ticket attachment")
    snapshot = _snapshot(attachment)
    AttachmentProducer.send_ticket_attachment_created(tenant_id=tenant_id, payload=snapshot)
    return attachment


def get_ticket_attachment(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    attachment_id: uuid.UUID,
) -> TicketAttachment:
    """Retrieve a single ticket attachment by ID within a tenant and ticket context."""
    attachment = (
        db.query(TicketAttachment)
        .filter(
            TicketAttachment.id == attachment_id,
            TicketAttachment.tenant_id == tenant_id,
            TicketAttachment.ticket_id == ticket_id,
        )
        .first()
    )
    if not attachment:
        logger.info(
            "Ticket attachment not found: tenant_id=%s, ticket_id=%s, attachment_id=%s",
            tenant_id,
            ticket_id,
            attachment_id,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket attachment not found")
    return attachment


def delete_ticket_attachment(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    attachment_id: uuid.UUID,
) -> None:
    """Delete a ticket attachment and publish a deletion event."""
    attachment = get_ticket_attachment(
        db, tenant_id=tenant_id, ticket_id=ticket_id, attachment_id=attachment_id
    )
    db.delete(attachment)
    commit_or_raise(db, action="delete ticket attachment")
    # Publish deletion event with timestamp
    AttachmentProducer.send_ticket_attachment_deleted(
        tenant_id=tenant_id,
        deleted_dt=datetime.utcnow().isoformat(),
    )
    return None