"""
SQLAlchemy model for TicketAudit.

This model captures append-only audit events for tickets. Each row
records a discrete event such as status change, priority change, tag
addition, field update, message addition, and AI interactions. The
model stores the actor information, optional AI session linkage, and
before/after snapshots of the changed properties. Audit events are
immutable and are scoped by tenant and ticket.
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
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketAudit(Base):
    """ORM model for the ``ticket_audit`` table."""

    __tablename__ = "ticket_audit"
    __table_args__ = (
        # Composite foreign key enforcing tenant safety for ticket linkage
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            name="fk_ticket_audit_ticket_tenant",
            ondelete="CASCADE",
        ),
        # Foreign key for actor contact with tenant guard
        ForeignKeyConstraint(
            ["actor_contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_ticket_audit_actor_contact_tenant",
            ondelete="SET NULL",
        ),
        # Foreign key for actor user with tenant guard
        ForeignKeyConstraint(
            ["tenant_id", "actor_user_id"],
            ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
            name="fk_ticket_audit_actor_user_tenant",
            ondelete="SET NULL",
        ),
        UniqueConstraint("id", "tenant_id", name="ux_ticket_audit_id_tenant"),
        CheckConstraint(
            "actor_type IN ('contact','agent','system','ai')",
            name="ck_ticket_audit_actor_type",
        ),
        # Descending index must be expressed in the index expression (not via kwargs)
        Index(
            "ix_ticket_audit_tenant_ticket_occurred",
            "tenant_id",
            "ticket_id",
            text("occurred_at DESC"),
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    ticket_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)

    actor_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    actor_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    ai_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<TicketAudit id={self.id} tenant_id={self.tenant_id} ticket_id={self.ticket_id} "
            f"event_type={self.event_type} actor_type={self.actor_type}>"
        )
