"""
SQLAlchemy model for TicketParticipant.

This model represents participants on a support ticket.  Participants
may be contacts (external customers) or agents (internal users) and
carry a role describing their relationship to the ticket (requester,
CC, or follower).  Participants are scoped to a tenant and a ticket.

Uniqueness constraints ensure that a given contact or user cannot be
added multiple times with the same role.  Check constraints enforce
the allowed values for participant_type and role.  Foreign keys
associate the participant with the ticket, contact, and tenant user
shadow tables for tenant‑safe joins.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketParticipant(Base):
    """ORM model for the ``ticket_participant`` table."""

    __tablename__ = "ticket_participant"
    __table_args__ = (
        # Composite foreign keys for tenant‑safe joins
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            name="fk_ticket_participant_ticket_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_ticket_participant_contact_tenant",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
            name="fk_ticket_participant_user_tenant",
            ondelete="SET NULL",
        ),
        # Uniqueness and indexing
        UniqueConstraint("id", "tenant_id", name="ux_ticket_participant_id_tenant"),
        UniqueConstraint(
            "tenant_id", "ticket_id", "contact_id", "role",
            name="ux_ticket_participant_unique_contact",
        ),
        UniqueConstraint(
            "tenant_id", "ticket_id", "user_id", "role",
            name="ux_ticket_participant_unique_user",
        ),
        Index("ix_ticket_participant_tenant_ticket", "tenant_id", "ticket_id"),
        # Check constraints for enumerated fields
        CheckConstraint(
            "participant_type IN ('contact','agent')",
            name="ck_ticket_participant_type",
        ),
        CheckConstraint(
            "role IN ('requester','cc','follower')",
            name="ck_ticket_participant_role",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    ticket_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    participant_type: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    role: Mapped[str] = mapped_column(String(50), nullable=False, default="cc")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TicketParticipant id={self.id} tenant_id={self.tenant_id} ticket_id={self.ticket_id} "
            f"type={self.participant_type} role={self.role}>"
        )