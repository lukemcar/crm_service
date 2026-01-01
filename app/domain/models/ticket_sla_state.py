"""
SQLAlchemy model for Ticket SLA State.

This model stores computed SLA deadlines and breach flags for each
ticket.  A ``ticket_sla_state`` row is created when an SLA policy is
applied to a ticket and updated whenever timers are recalculated by
orchestration.  It is mainly read-only for tenant and admin APIs,
though internal services may update it.  Each state belongs to a
tenant and references both a ticket and an optional SLA policy.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    String,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketSlaState(Base):
    """ORM model for the ``ticket_sla_state`` table."""

    __tablename__ = "ticket_sla_state"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_ticket_sla_state_id_tenant"),
        UniqueConstraint(
            "tenant_id", "ticket_id", name="ux_ticket_sla_state_unique"
        ),
        ForeignKeyConstraint([
            "ticket_id"
        ], ["dyno_crm.ticket.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint([
            "sla_policy_id"
        ], ["dyno_crm.sla_policy.id"], ondelete="SET NULL"),
        ForeignKeyConstraint(
            ["sla_policy_id", "tenant_id"],
            ["dyno_crm.sla_policy.id", "dyno_crm.sla_policy.tenant_id"],
            ondelete="SET NULL",
        ),
        Index("ix_ticket_sla_state_tenant_ticket", "tenant_id", "ticket_id"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    sla_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    first_response_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_response_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    first_response_breached: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    next_response_breached: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    resolution_breached: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    last_computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TicketSlaState id={self.id} tenant_id={self.tenant_id} "
            f"ticket_id={self.ticket_id} sla_policy_id={self.sla_policy_id}>"
        )
