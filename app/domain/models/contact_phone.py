# app/models/contact_phone.py
"""SQLAlchemy model for ContactPhone.

Schema: dyno_crm.contact_phone
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ContactPhone(Base):
    __tablename__ = "contact_phone"
    __table_args__ = (
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_phone_contact_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_contact_phone_tenant_contact", "tenant_id", "contact_id"),
        Index(
            "ix_contact_phone_tenant_phone_e164",
            "tenant_id",
            "phone_e164",
            postgresql_where=text("phone_e164 IS NOT NULL"),
        ),
        Index("ix_contact_phone_tenant_phone_raw", "tenant_id", "phone_raw"),
        Index(
            "ux_contact_phone_contact_phone_e164",
            "tenant_id",
            "contact_id",
            "phone_e164",
            unique=True,
            postgresql_where=text("phone_e164 IS NOT NULL"),
        ),
        Index(
            "ux_contact_phone_primary_per_contact",
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

    phone_raw: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_e164: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    phone_type: Mapped[str] = mapped_column(String(50), nullable=False, default="mobile")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_sms_capable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Tenant-safe relationship join (avoids AmbiguousForeignKeysError)
    contact: Mapped["Contact"] = relationship(
        "Contact",
        primaryjoin="and_(Contact.id==ContactPhone.contact_id, Contact.tenant_id==ContactPhone.tenant_id)",
        foreign_keys="(ContactPhone.contact_id, ContactPhone.tenant_id)",
        back_populates="phones",
    )

    def __repr__(self) -> str:
        return (
            f"<ContactPhone id={self.id} tenant_id={self.tenant_id} "
            f"contact_id={self.contact_id} phone={self.phone_raw}>"
        )
