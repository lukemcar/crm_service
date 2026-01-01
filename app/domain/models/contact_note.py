# app/models/contact_note.py
"""SQLAlchemy model for ContactNote.

Historical notes collected for a contact. Internal to the tenant.

Schema: dyno_crm.contact_note
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ContactNote(Base):
    __tablename__ = "contact_note"
    __table_args__ = (
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_note_contact_tenant",
            ondelete="CASCADE",
        ),
        Index("ix_contact_note_tenant_contact_noted_at", "tenant_id", "contact_id", "noted_at"),
        Index("ix_contact_note_tenant_noted_at", "tenant_id", "noted_at"),
        Index("ix_contact_note_tenant_note_type", "tenant_id", "note_type"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.contact.id", ondelete="CASCADE"),
        nullable=False,
    )

    note_type: Mapped[str] = mapped_column(String(50), nullable=False, default="note")
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    noted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    source_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Tenant-safe relationship join (avoids AmbiguousForeignKeysError)
    contact: Mapped["Contact"] = relationship(
        "Contact",
        primaryjoin="and_(Contact.id==ContactNote.contact_id, Contact.tenant_id==ContactNote.tenant_id)",
        foreign_keys="(ContactNote.contact_id, ContactNote.tenant_id)",
        back_populates="notes",
    )

    def __repr__(self) -> str:
        return (
            f"<ContactNote id={self.id} tenant_id={self.tenant_id} "
            f"contact_id={self.contact_id} noted_at={self.noted_at}>"
        )
