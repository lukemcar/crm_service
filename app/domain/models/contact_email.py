# app/models/contact_email.py
"""SQLAlchemy model for ContactEmail.

Schema: dyno_crm.contact_email
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ContactEmail(Base):
    __tablename__ = "contact_email"
    __table_args__ = (
        # Tenant-safe composite foreign key. This is the FK path we want SQLAlchemy to use
        # for relationship joins.
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_email_contact_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_contact_email_tenant_contact", "tenant_id", "contact_id"),
        Index("ix_contact_email_tenant_email", "tenant_id", text("lower(email)")),
        Index(
            "ux_contact_email_contact_email",
            "tenant_id",
            "contact_id",
            text("lower(email)"),
            unique=True,
        ),
        # One primary per contact (partial unique index)
        Index(
            "ux_contact_email_primary_per_contact",
            "tenant_id",
            "contact_id",
            unique=True,
            postgresql_where=text("is_primary = TRUE"),
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
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # -----------------------------------------------------------------
    # Relationship to Contact
    #
    # IMPORTANT:
    # The schema has multiple FK paths:
    #   - contact_id -> contact.id
    #   - (contact_id, tenant_id) -> (contact.id, contact.tenant_id)
    #
    # Without explicit foreign_keys/primaryjoin SQLAlchemy raises:
    #   AmbiguousForeignKeysError
    #
    # We use the composite join for tenant-safe navigation.
    # -----------------------------------------------------------------
    contact: Mapped["Contact"] = relationship(
        "Contact",
        primaryjoin="and_(Contact.id==ContactEmail.contact_id, Contact.tenant_id==ContactEmail.tenant_id)",
        foreign_keys="(ContactEmail.contact_id, ContactEmail.tenant_id)",
        back_populates="emails",
    )

    def __repr__(self) -> str:
        return f"<ContactEmail id={self.id} tenant_id={self.tenant_id} contact_id={self.contact_id} email={self.email}>"
