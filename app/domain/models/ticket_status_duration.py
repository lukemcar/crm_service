"""
SQLAlchemy model definitions for ticket status duration facts.

This module defines the ``TicketStatusDuration`` model representing
individual intervals that a ticket spent in a particular status.  Each
row records the status, start and end timestamps, and the computed
duration in seconds.  The table is tenant‑scoped and enforces
composite uniqueness on ``(tenant_id, ticket_id, id)``.  Valid status
values are constrained to the same set as defined on the ``ticket``
table.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    String,
    BigInteger,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.db import Base


class TicketStatusDuration(Base):
    """Database model for ticket status duration facts.

    Each row records a continuous interval during which a ticket remained
    in a given status.  The ``duration_seconds`` column can be
    computed by background processing based on audit events.  The
    ``ended_at`` column may be null for currently active status
    intervals.
    """

    __tablename__ = "ticket_status_duration"

    id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    ticket_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Ticket status value at the time of the interval. Must match
    # allowed status values from ticket CK constraint.
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint('id', 'tenant_id', name='ux_ticket_status_duration_id_tenant'),
        ForeignKeyConstraint(['ticket_id'], ['ticket.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['ticket_id', 'tenant_id'], ['ticket.id', 'ticket.tenant_id'], ondelete='CASCADE'),
        CheckConstraint(
            "status IN ('new','open','pending','on_hold','solved','closed')",
            name='ck_ticket_status_duration_status',
        ),
        Index('ix_ticket_status_duration_tenant_ticket', 'tenant_id', 'ticket_id'),
        {"schema": "dyno_crm"},
    )

    def __repr__(self) -> str:
        return (
            f"TicketStatusDuration(id={self.id}, tenant_id={self.tenant_id}, ticket_id={self.ticket_id}, "
            f"status={self.status}, started_at={self.started_at}, ended_at={self.ended_at}, "
            f"duration_seconds={self.duration_seconds})"
        )


__all__ = ["TicketStatusDuration"]