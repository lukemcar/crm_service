# app/models/contact_email.py
"""SQLAlchemy model for ContactEmail.

Schema: dyno_crm.contact_email
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class ContactEmail(Base):
    __tablename__ = "contact_email"
    __table_args__ = (
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_email_contact_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_contact_email_tenant_contact", "tenant_id", "contact_id"),
        Index("ix_contact_email_tenant_email", "tenant_id", func.lower("email")),
        Index(
            "ux_contact_email_contact_email",
            "tenant_id",
            "contact_id",
            func.lower("email"),
            unique=True,
        ),
        Index(
            "ux_contact_email_primary_per_contact",
            "tenant_id",
            "contact_id",
            unique=True,
            postgresql_where=(func.coalesce("is_primary", False) == True),  # noqa: E712
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.contact.id", ondelete="CASCADE"),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_type: Mapped[str] = mapped_column(String(50), nullable=False, default="work")

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="emails")

    def __repr__(self) -> str:
        return f"<ContactEmail id={self.id} tenant_id={self.tenant_id} contact_id={self.contact_id} email={self.email}>"
