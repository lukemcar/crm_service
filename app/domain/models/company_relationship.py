# app/models/company_relationship.py
"""SQLAlchemy model for CompanyRelationship (dyno_crm.company_relationship).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


_ALLOWED_ROLES = (
    'client','supplier','vendor','partner','reseller','manufacturer','parent','subsidiary','competitor',
    'investor','portfolio_company','franchisee','franchisor','affiliate','buyer','seller','advisor',
    'client_company','consultant','lender','borrower','donor','nonprofit','sponsor','sponsee','debtor',
    'creditor','other'
)


class CompanyRelationship(Base):
    __tablename__ = "company_relationship"
    __table_args__ = (
        ForeignKeyConstraint(
            ["from_company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_relationship_from_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["to_company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_relationship_to_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint("from_company_id <> to_company_id", name="ck_company_relationship_not_self"),
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="ck_company_relationship_dates",
        ),
        CheckConstraint(
            f"from_role IN ({', '.join([repr(v) for v in _ALLOWED_ROLES])}) "
            f"AND to_role IN ({', '.join([repr(v) for v in _ALLOWED_ROLES])})",
            name="ck_company_relationship_role_values",
        ),
        Index("ix_company_relationship_tenant_from", "tenant_id", "from_company_id"),
        Index("ix_company_relationship_tenant_to", "tenant_id", "to_company_id"),
        Index(
            "ux_company_relationship_unique",
            "tenant_id",
            "from_company_id",
            "to_company_id",
            "from_role",
            "to_role",
            unique=True,
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    from_company_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    to_company_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    from_role: Mapped[str] = mapped_column(String(50), nullable=False)
    to_role: Mapped[str] = mapped_column(String(50), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    start_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    from_company: Mapped["Company"] = relationship(
        "Company",
        primaryjoin="and_(Company.id==CompanyRelationship.from_company_id, Company.tenant_id==CompanyRelationship.tenant_id)",
        foreign_keys="(CompanyRelationship.from_company_id, CompanyRelationship.tenant_id)",
        back_populates="relationships_from",
        overlaps="to_company,relationships_to",
    )

    to_company: Mapped["Company"] = relationship(
        "Company",
        primaryjoin="and_(Company.id==CompanyRelationship.to_company_id, Company.tenant_id==CompanyRelationship.tenant_id)",
        foreign_keys="(CompanyRelationship.to_company_id, CompanyRelationship.tenant_id)",
        back_populates="relationships_to",
        overlaps="from_company,relationships_from",
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyRelationship id={self.id} tenant_id={self.tenant_id} "
            f"from={self.from_company_id}({self.from_role}) to={self.to_company_id}({self.to_role})>"
        )
