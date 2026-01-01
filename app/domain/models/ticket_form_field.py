"""
SQLAlchemy model for TicketFormField (dyno_crm.ticket_form_field).

This model defines the association between a ticket form and a custom
field definition.  Each row indicates that a particular field is
included on a given form and specifies the order in which it should
appear.  The database enforces uniqueness of the combination of
``ticket_form_id`` and ``ticket_field_def_id`` per tenant, as well as a
unique display order within a form.  Audit metadata tracks when the
association was created and by whom.

The DDL defined in ``002_support_domain_schema.sql`` is the source of
truth for constraints and indexes; this model mirrors those rules.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketFormField(Base):
    """ORM model for the ``ticket_form_field`` table.

    A ticket form field record links a custom field definition to a
    specific ticket form.  The ``display_order`` determines the order
    that fields appear on the form.  This table is tenant scoped via
    ``tenant_id`` and participates in composite foreign key
    relationships to ensure tenant consistency.
    """

    __tablename__ = "ticket_form_field"
    __table_args__ = (
        # enforce unique id per tenant
        UniqueConstraint(
            "id",
            "tenant_id",
            name="ux_ticket_form_field_id_tenant",
        ),
        # unique association between form and field per tenant
        UniqueConstraint(
            "tenant_id",
            "ticket_form_id",
            "ticket_field_def_id",
            name="ux_ticket_form_field_unique",
        ),
        # unique display order per form per tenant
        UniqueConstraint(
            "tenant_id",
            "ticket_form_id",
            "display_order",
            name="ux_ticket_form_field_order",
        ),
        # index for tenant lookups
        Index("ix_ticket_form_field_tenant", "tenant_id"),
        # composite foreign keys to enforce tenant consistency
        ForeignKeyConstraint(
            ["ticket_form_id", "tenant_id"],
            ["ticket_form.id", "ticket_form.tenant_id"],
            ondelete="CASCADE",
            name="fk_ticket_form_field_form_tenant",
        ),
        ForeignKeyConstraint(
            ["ticket_field_def_id", "tenant_id"],
            ["ticket_field_def.id", "ticket_field_def.tenant_id"],
            ondelete="CASCADE",
            name="fk_ticket_form_field_field_tenant",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    ticket_form_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    ticket_field_def_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - trivial repr
        return (
            f"<TicketFormField id={self.id} tenant_id={self.tenant_id} "
            f"form_id={self.ticket_form_id} field_def_id={self.ticket_field_def_id} "
            f"order={self.display_order}>"
        )


__all__ = ["TicketFormField"]
