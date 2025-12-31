# app/models/company_email.py
"""SQLAlchemy model for CompanyEmail (dyno_crm.company_email).

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


class CompanyEmail(Base):
    __tablename__ = "company_email"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_email_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "email_type IN ('work','billing','support','sales','other')",
            name="ck_company_email_type",
        ),
        Index("ix_company_email_tenant_company", "tenant_id", "company_id"),
        Index("ix_company_email_tenant_email", "tenant_id", text("lower(email)")),
        Index(
            "ux_company_email_company_email",
            "tenant_id",
            "company_id",
            text("lower(email)"),
            unique=True,
        ),
        Index(
            "ux_company_email_primary_per_company",
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

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_type: Mapped[str] = mapped_column(String(50), nullable=False, default="work")

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company: Mapped["Company"] = relationship(
        "Company",
        primaryjoin="and_(Company.id==CompanyEmail.company_id, Company.tenant_id==CompanyEmail.tenant_id)",
        foreign_keys="(CompanyEmail.company_id, CompanyEmail.tenant_id)",
        back_populates="emails",
    )

    def __repr__(self) -> str:
        return f"<CompanyEmail id={self.id} tenant_id={self.tenant_id} company_id={self.company_id} email={self.email}>"
