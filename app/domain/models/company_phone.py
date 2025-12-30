# app/models/company_phone.py
"""SQLAlchemy model for CompanyPhone (dyno_crm.company_phone).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class CompanyPhone(Base):
    __tablename__ = "company_phone"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_phone_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "phone_type IN ('main','support','sales','billing','fax','other')",
            name="ck_company_phone_type",
        ),
        Index("ix_company_phone_tenant_company", "tenant_id", "company_id"),
        Index("ix_company_phone_tenant_phone_raw", "tenant_id", "phone_raw"),
        Index(
            "ix_company_phone_tenant_phone_e164",
            "tenant_id",
            "phone_e164",
            postgresql_where=text("phone_e164 IS NOT NULL"),
        ),
        Index(
            "ux_company_phone_company_phone_e164",
            "tenant_id",
            "company_id",
            "phone_e164",
            unique=True,
            postgresql_where=text("phone_e164 IS NOT NULL"),
        ),
        Index(
            "ux_company_phone_primary_per_company",
            "tenant_id",
            "company_id",
            unique=True,
            postgresql_where=text("is_primary IS TRUE"),
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.company.id", ondelete="CASCADE"),
        nullable=False,
    )

    phone_raw: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_e164: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone_ext: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    phone_type: Mapped[str] = mapped_column(String(50), nullable=False, default="main")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_sms_capable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="phones")

    def __repr__(self) -> str:
        return f"<CompanyPhone id={self.id} tenant_id={self.tenant_id} company_id={self.company_id} phone={self.phone_raw}>"
