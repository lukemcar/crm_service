# app/models/company_address.py
"""SQLAlchemy model for CompanyAddress (dyno_crm.company_address).

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


class CompanyAddress(Base):
    __tablename__ = "company_address"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_address_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "address_type IN ('office','billing','shipping','warehouse','receivings','other')",
            name="ck_company_address_type",
        ),
        Index("ix_company_address_tenant_company", "tenant_id", "company_id"),
        Index(
            "ux_company_address_primary_per_company",
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

    address_type: Mapped[str] = mapped_column(String(50), nullable=False, default="office")
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

    company: Mapped["Company"] = relationship(
        "Company",
        primaryjoin="and_(Company.id==CompanyAddress.company_id, Company.tenant_id==CompanyAddress.tenant_id)",
        foreign_keys="(CompanyAddress.company_id, CompanyAddress.tenant_id)",
        back_populates="addresses",
    )

    def __repr__(self) -> str:
        return f"<CompanyAddress id={self.id} tenant_id={self.tenant_id} company_id={self.company_id} type={self.address_type}>"
