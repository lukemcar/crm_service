# app/models/company_note.py
"""SQLAlchemy model for CompanyNote (dyno_crm.company_note).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class CompanyNote(Base):
    __tablename__ = "company_note"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_note_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "note_type IN ('note','call','meeting','email','sms','other')",
            name="ck_company_note_type",
        ),
        Index("ix_company_note_tenant_company_noted_at", "tenant_id", "company_id", "noted_at"),
        Index("ix_company_note_tenant_noted_at", "tenant_id", "noted_at"),
        Index("ix_company_note_tenant_note_type", "tenant_id", "note_type"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.company.id", ondelete="CASCADE"),
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

    company: Mapped["Company"] = relationship("Company", back_populates="notes")

    def __repr__(self) -> str:
        return f"<CompanyNote id={self.id} tenant_id={self.tenant_id} company_id={self.company_id} noted_at={self.noted_at}>"
