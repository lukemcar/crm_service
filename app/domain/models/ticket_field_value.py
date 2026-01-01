"""
SQLAlchemy model for TicketFieldValue (dyno_crm.ticket_field_value).

This model stores the actual values for custom fields on a ticket.
Each row links a ticket to a field definition and stores one of
several possible value types.  Only one of the value columns should
be non‑null for a given record, depending on the field's data type.
The model enforces tenant scoping and unique (ticket_id,
ticket_field_def_id) combinations within a tenant.  Audit fields
record when the value was created or last updated and by whom.

The DDL defined in ``002_support_domain_schema.sql`` is the source of
truth for constraints and indexes; this model mirrors those rules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketFieldValue(Base):
    """ORM model for the ``ticket_field_value`` table.

    Stores the value of a custom field for a specific ticket.  The
    ``ticket_field_def_id`` points to the definition, and exactly one
    of the ``value_*`` columns should be populated according to the
    field's type.  Tenant scoping is enforced via ``tenant_id`` and
    composite foreign keys.  Uniqueness of the (ticket_id,
    ticket_field_def_id) tuple per tenant prevents duplicate values.
    """

    __tablename__ = "ticket_field_value"
    __table_args__ = (
        # enforce unique id per tenant
        UniqueConstraint("id", "tenant_id", name="ux_ticket_field_value_id_tenant"),
        # unique value per ticket and field definition per tenant
        UniqueConstraint(
            "tenant_id",
            "ticket_id",
            "ticket_field_def_id",
            name="ux_ticket_field_value_unique",
        ),
        # index for tenant and ticket lookups
        Index("ix_ticket_field_value_tenant_ticket", "tenant_id", "ticket_id"),
        # composite foreign keys to enforce tenant consistency
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["ticket.id", "ticket.tenant_id"],
            ondelete="CASCADE",
            name="fk_ticket_field_value_ticket_tenant",
        ),
        ForeignKeyConstraint(
            ["ticket_field_def_id", "tenant_id"],
            ["ticket_field_def.id", "ticket_field_def.tenant_id"],
            ondelete="CASCADE",
            name="fk_ticket_field_value_field_tenant",
        ),
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
    ticket_field_def_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )

    # value columns - only one should be non-null per record
    value_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    value_bool: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    value_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    value_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - trivial repr
        return (
            f"<TicketFieldValue id={self.id} tenant_id={self.tenant_id} "
            f"ticket_id={self.ticket_id} field_def_id={self.ticket_field_def_id}>"
        )


__all__ = ["TicketFieldValue"]