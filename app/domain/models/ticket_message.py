"""
SQLAlchemy model for TicketMessage.

This model represents individual messages within a ticket's
conversation thread.  Messages are append‑only to preserve history.
They record who authored the message (contact, agent, system or AI),
whether the message is public or internal, the channel through which
the message was received or sent, and any external reference keys
used for idempotency.  A JSON ``metadata`` field stores non‑secret
provider payload snapshots.  Messages are scoped by tenant and
ticket.  Enumerated fields enforce allowed values for author_type
and channel_type.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Boolean,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketMessage(Base):
    """ORM model for the ``ticket_message`` table."""

    __tablename__ = "ticket_message"
    __table_args__ = (
        # Composite foreign keys
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            name="fk_ticket_message_ticket_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["author_contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_ticket_message_author_contact_tenant",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "author_user_id"],
            ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
            name="fk_ticket_message_author_user_tenant",
            ondelete="SET NULL",
        ),
        UniqueConstraint("id", "tenant_id", name="ux_ticket_message_id_tenant"),
        Index(
            "ix_ticket_message_tenant_ticket_created",
            "tenant_id",
            "ticket_id",
            "created_at",
        ),\
        Index(
            "ix_ticket_message_tenant_created",
            "tenant_id",
            text("created_at DESC"),
        ),
        Index(
            "ix_ticket_message_tenant_external_ref",
            "tenant_id",
            "channel_type",
            "external_ref",
            postgresql_where=text("external_ref IS NOT NULL"),
        ),
        CheckConstraint(
            "author_type IN ('contact','agent','system','ai')",
            name="ck_ticket_message_author_type",
        ),
        CheckConstraint(
            "channel_type IN ('email','web','chat','sms','voice','api','internal','social')",
            name="ck_ticket_message_channel_type",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    ticket_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    author_type: Mapped[str] = mapped_column(String(50), nullable=False)
    author_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    author_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    author_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False, default="internal")
    external_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Renamed from `metadata` to avoid conflict with SQLAlchemy's reserved attribute
    # The database column name remains "metadata"; only the Python attribute name changes.
    provider_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSON, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TicketMessage id={self.id} tenant_id={self.tenant_id} ticket_id={self.ticket_id} "
            f"author_type={self.author_type} is_public={self.is_public}>"
        )