# app/models/contact_address.py
"""SQLAlchemy model for ContactAddress.

Schema: dyno_crm.contact_address
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ContactAddress(Base):
    __tablename__ = "contact_address"
    __table_args__ = (
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_address_contact_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_contact_address_tenant_contact", "tenant_id", "contact_id"),
        Index(
            "ux_contact_address_primary_per_contact",
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

    address_type: Mapped[str] = mapped_column(String(50), nullable=False, default="home")
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    line3: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="US")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Tenant-safe relationship join (avoids AmbiguousForeignKeysError)
    contact: Mapped["Contact"] = relationship(
        "Contact",
        primaryjoin="and_(Contact.id==ContactAddress.contact_id, Contact.tenant_id==ContactAddress.tenant_id)",
        foreign_keys="(ContactAddress.contact_id, ContactAddress.tenant_id)",
        back_populates="addresses",
    )

    def __repr__(self) -> str:
        return (
            f"<ContactAddress id={self.id} tenant_id={self.tenant_id} "
            f"contact_id={self.contact_id} type={self.address_type}>"
        )
