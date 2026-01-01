"""SQLAlchemy model for ticket time entries.

This table records time spent by agents on tickets. Each row captures
who logged the time (via a tenant-scoped user_id), how many minutes
were spent, and optional categorization such as work type and notes.
Audit fields record when the entry was created and by whom. Time
entries are tenant scoped and linked to a specific ticket. Deleting a
ticket cascades to delete its time entries.
"""

import datetime as _dt
import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
    Index,
    String,
    Integer,
    Text,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class TicketTimeEntry(Base):
    """Model for the ``ticket_time_entry`` table.

    Each entry records the amount of time spent by a user on a ticket. The
    entry is tenant scoped and enforces that ``minutes_spent`` is non-negative.
    Optional fields allow capturing the type of work performed, notes, and
    start/end timestamps. Time entries are immutable once created from the
    perspective of who created them, but administrators may update entries
    for correction purposes.
    """

    __tablename__ = "ticket_time_entry"
    __table_args__ = (
        # Ensure time entry ids are unique per tenant
        UniqueConstraint("id", "tenant_id", name="ux_ticket_time_entry_id_tenant"),
        # Composite foreign key linking ticket_id and tenant_id to the ticket table
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["ticket.id", "ticket.tenant_id"],
            ondelete="CASCADE",
            name="fk_ticket_time_entry_ticket_tenant",
        ),
        # Composite foreign key linking tenant_id and user_id to tenant_user_shadow
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["tenant_user_shadow.tenant_id", "tenant_user_shadow.user_id"],
            ondelete="SET NULL",
            name="fk_ticket_time_entry_user_tenant",
        ),
        # Index for efficient lookup by tenant and ticket
        Index("ix_ticket_time_entry_tenant_ticket", "tenant_id", "ticket_id"),
        # Minutes spent must be non-negative
        CheckConstraint("minutes_spent >= 0", name="ck_ticket_time_entry_minutes"),
        {"schema": "dyno_crm"},
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    ticket_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ticket.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )
    # minutes spent must be >= 0 (enforced by check constraint)
    minutes_spent = Column(Integer, nullable=False)
    work_type = Column(String(50), nullable=True)
    note = Column(String(500), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_dt.datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    # Relationship-level FKs are defined in table args via ForeignKeyConstraint

    def __repr__(self) -> str:
        return f"<TicketTimeEntry id={self.id} tenant={self.tenant_id} ticket={self.ticket_id}>"


__all__ = ["TicketTimeEntry"]