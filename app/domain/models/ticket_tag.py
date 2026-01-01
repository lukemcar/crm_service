"""
SQLAlchemy model for TicketTag.

This model represents simple tags applied to tickets.  Tags are
strings that can be attached to tickets for flexible categorisation
and filtering.  Tags are scoped to a tenant and a ticket.  A
uniqueness constraint prevents duplicate tags on a ticket (case
sensitive).  Timestamp and audit fields record when the tag was
created and by whom.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
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


class TicketTag(Base):
    """ORM model for the ``ticket_tag`` table."""

    __tablename__ = "ticket_tag"
    __table_args__ = (
        # Composite foreign keys for tenant‑safe joins
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"],
            name="fk_ticket_tag_ticket_tenant",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "tenant_id", name="ux_ticket_tag_id_tenant"),
        UniqueConstraint(
            "tenant_id", "ticket_id", "tag",
            name="ux_ticket_tag_unique",
        ),
        Index("ix_ticket_tag_tenant_tag", "tenant_id", "tag"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    ticket_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    tag: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TicketTag id={self.id} tenant_id={self.tenant_id} ticket_id={self.ticket_id} "
            f"tag={self.tag}>"
        )