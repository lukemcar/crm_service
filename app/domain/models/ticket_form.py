"""
SQLAlchemy model for TicketForm.

This model represents a custom ticket form that a tenant can define to
collect structured data when a ticket is created or updated.  Forms are
defined at the tenant level and consist of a name, optional
description, and active flag.  Each form may contain an ordered list
of fields defined in ``ticket_form_field``, but that linking is handled
in a separate model.  Forms support full CRUD operations via the API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketForm(Base):
    """ORM model for the ``ticket_form`` table."""

    __tablename__ = "ticket_form"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_ticket_form_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_ticket_form_tenant_name"),
        Index("ix_ticket_form_tenant", "tenant_id"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
            f"<TicketForm id={self.id} tenant_id={self.tenant_id} name={self.name}>"
        )