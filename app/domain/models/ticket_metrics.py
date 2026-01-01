"""
SQLAlchemy model definitions for ticket metrics.

This module defines the ``TicketMetrics`` model representing summary
statistics for individual tickets.  Each record stores counts of
replies and reopen events.  The table is tenant‑scoped and enforces
composite uniqueness on ``(tenant_id, ticket_id)`` to ensure that
each ticket has at most one metrics record.

The corresponding table DDL can be found in the support domain
migration ``002_support_domain_schema.sql``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base  # unused; kept for consistency

from app.core.db import Base


class TicketMetrics(Base):
    """Database model for ticket summary metrics.

    Each row stores counts of replies and reopen events for a single
    ticket.  This table is typically populated by background jobs that
    process audit logs and message events.  For tenants, this data is
    read‑only; admin endpoints may insert or update records for
    backfilling or manual corrections.
    """

    __tablename__ = "ticket_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Foreign key to the associated ticket.  Use composite FK for tenant
    # safety; defined via ForeignKeyConstraint in a CheckConstraint.
    ticket_id = Column(PGUUID(as_uuid=True), nullable=False)

    reply_count = Column(Integer, nullable=False, default=0)
    reopen_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint('id', 'tenant_id', name='ux_ticket_metrics_id_tenant'),
        UniqueConstraint('tenant_id', 'ticket_id', name='ux_ticket_metrics_unique'),
        ForeignKeyConstraint(['ticket_id'], ['ticket.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['ticket_id', 'tenant_id'], ['ticket.id', 'ticket.tenant_id'], ondelete='CASCADE'),
        {"schema": "dyno_crm"},
    )

    def __repr__(self) -> str:
        return (
            f"TicketMetrics(id={self.id}, tenant_id={self.tenant_id}, ticket_id={self.ticket_id}, "
            f"reply_count={self.reply_count}, reopen_count={self.reopen_count})"
        )


__all__ = ["TicketMetrics"]