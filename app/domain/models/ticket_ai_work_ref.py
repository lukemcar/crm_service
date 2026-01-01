"""
SQLAlchemy model for the ticket_ai_work_ref table.

This table stores pointers to AI Workforce sessions related to support tickets.
Each row links a ticket to a specific AI session, capturing metadata about
the agent key, purpose, status, outcome, confidence and timestamps. Entries
are typically created and updated by the AI integration layer; tenants can
only read these records. Admin/internal APIs may upsert records for
recovery or migration.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Numeric,
    UniqueConstraint,
    Index,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class TicketAiWorkRef(Base):
    """SQLAlchemy model for the ``ticket_ai_work_ref`` table."""

    __tablename__ = "ticket_ai_work_ref"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_ticket_ai_work_ref_id_tenant"),
        # Unique ai_session_id per tenant to prevent duplicates
        UniqueConstraint(
            "tenant_id",
            "ai_session_id",
            name="ux_ticket_ai_work_ref_unique_session",
        ),
        # Foreign key to ticket with tenant scoping
        ForeignKeyConstraint([
            "ticket_id",
        ], ["dyno_crm.ticket.id"], name="fk_ticket_ai_work_ref_ticket", ondelete="CASCADE"),
        ForeignKeyConstraint([
            "ticket_id",
            "tenant_id",
        ], ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"], name="fk_ticket_ai_work_ref_ticket_tenant", ondelete="CASCADE"),
        # Indexes for querying by ticket and agent key
        Index(
            "ix_ticket_ai_work_ref_tenant_ticket",
            "tenant_id",
            "ticket_id",
            "requested_at",
        ),
        Index(
            "ix_ticket_ai_work_ref_tenant_agent",
            "tenant_id",
            "agent_key",
            "requested_at",
        ),
        {"schema": "dyno_crm"},
    )

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)

    # Foreign key to ticket
    ticket_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)

    # AI session and agent
    ai_session_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    agent_key: str = Column(String(120), nullable=False)
    purpose: str = Column(String(100), nullable=False)

    # Status and outcome
    status: str = Column(String(50), nullable=False, default="started")
    outcome: Optional[str] = Column(String(50))
    confidence: Optional[float] = Column(Numeric(5, 4))

    # Timing fields
    requested_at: datetime = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    completed_at: Optional[datetime] = Column(DateTime(timezone=True))

    # Audit
    created_by: Optional[str] = Column(String(100))

    def __repr__(self) -> str:
        return (
            f"<TicketAiWorkRef id={self.id} ticket_id={self.ticket_id} "
            f"ai_session_id={self.ai_session_id} tenant_id={self.tenant_id}>"
        )


__all__ = ["TicketAiWorkRef"]