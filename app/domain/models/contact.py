# app/models/contact.py
"""SQLAlchemy model for Contact.

Represents a person record in the CRM. Child collections such as emails,
phones, addresses, social profiles, and notes are stored in separate tables.

Schema: dyno_crm.contact
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Contact(Base):
    __tablename__ = "contact"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_contact_id_tenant"),
        Index("ix_contact_tenant", "tenant_id"),
        Index("ix_contact_tenant_last_first", "tenant_id", "last_name", "first_name"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    maiden_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prefix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    emails: Mapped[List["ContactEmail"]] = relationship(
        "ContactEmail",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    phones: Mapped[List["ContactPhone"]] = relationship(
        "ContactPhone",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    addresses: Mapped[List["ContactAddress"]] = relationship(
        "ContactAddress",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    social_profiles: Mapped[List["ContactSocialProfile"]] = relationship(
        "ContactSocialProfile",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    notes: Mapped[List["ContactNote"]] = relationship(
        "ContactNote",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(ContactNote.noted_at)",
    )

    def __repr__(self) -> str:
        return f"<Contact id={self.id} tenant_id={self.tenant_id} name={self.first_name} {self.last_name}>"
