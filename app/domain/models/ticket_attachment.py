"""
SQLAlchemy model for TicketAttachment.

This model represents files attached to tickets or specific ticket
messages.  Attachments store only metadata and pointers to files
hosted in an external storage provider.  They are scoped by
tenant and ticket.  A ticket attachment may optionally be linked
to a specific ticket message.  Append‑only semantics apply; the
CRM does not update attachments once created.  Composite foreign
keys enforce tenant‑safe relationships to tickets and messages,
and a check constraint restricts the ``storage_provider`` field
to known values.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketAttachment(Base):
    """ORM model for the ``ticket_attachment`` table."""

    __tablename__ = "ticket_attachment"
    __table_args__ = (
        # Composite foreign key enforcing tenant safety for ticket linkage
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            name="fk_ticket_attachment_ticket_tenant",
            ondelete="CASCADE",
        ),
        # Composite foreign key to ticket_message (optional) with tenant guard
        ForeignKeyConstraint(
            ["ticket_message_id", "tenant_id"],
            ["dyno_crm.ticket_message.id", "dyno_crm.ticket_message.tenant_id"],
            name="fk_ticket_attachment_message_tenant",
            ondelete="SET NULL",
        ),
        UniqueConstraint("id", "tenant_id", name="ux_ticket_attachment_id_tenant"),
        Index("ix_ticket_attachment_tenant_ticket", "tenant_id", "ticket_id"),
        CheckConstraint(
            "storage_provider IS NULL OR storage_provider IN ('s3','gcs','azure','local','other')",
            name="ck_ticket_attachment_storage_provider",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    ticket_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    ticket_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    storage_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TicketAttachment id={self.id} tenant_id={self.tenant_id} "
            f"ticket_id={self.ticket_id} file_name={self.file_name}>"
        )
