"""
SQLAlchemy model for TicketAssignment.

This model represents assignment history for tickets.  Each row records
when a ticket was assigned or reassigned to a group or user, who
performed the assignment, an optional reason, and a reference to an AI
session if the assignment was performed by an AI agent.  The model
enforces tenant safety via composite foreign keys and is append-only;
assignments are not updated once created.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketAssignment(Base):
    """ORM model for the ``ticket_assignment`` table."""

    __tablename__ = "ticket_assignment"
    __table_args__ = (
        # Composite foreign key enforcing tenant safety for ticket linkage
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            name="fk_ticket_assignment_ticket_tenant",
            ondelete="CASCADE",
        ),
        # Foreign key for assigned group with tenant guard
        ForeignKeyConstraint(
            ["assigned_group_id", "tenant_id"],
            ["dyno_crm.tenant_group_shadow.id", "dyno_crm.tenant_group_shadow.tenant_id"],
            name="fk_ticket_assignment_group_tenant",
            ondelete="SET NULL",
        ),
        # Foreign key for assigned user with tenant guard
        ForeignKeyConstraint(
            ["tenant_id", "assigned_user_id"],
            ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
            name="fk_ticket_assignment_user_tenant",
            ondelete="SET NULL",
        ),
        # Foreign key for who performed the assignment
        ForeignKeyConstraint(
            ["tenant_id", "assigned_by_user_id"],
            ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
            name="fk_ticket_assignment_assigned_by_user_tenant",
            ondelete="SET NULL",
        ),
        UniqueConstraint("id", "tenant_id", name="ux_ticket_assignment_id_tenant"),
        # Descending index must be expressed in the index expression (not via kwargs)
        Index(
            "ix_ticket_assignment_tenant_ticket_created",
            "tenant_id",
            "ticket_id",
            text("created_at DESC"),
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    ticket_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    assigned_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    assigned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    assigned_by_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TicketAssignment id={self.id} tenant_id={self.tenant_id} ticket_id={self.ticket_id} "
            f"assigned_group_id={self.assigned_group_id} assigned_user_id={self.assigned_user_id}>"
        )
