# app/models/contact_company_relationship.py
"""SQLAlchemy model for ContactCompanyRelationship (dyno_crm.contact_company_relationship).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


_ALLOWED_CONTACT_COMPANY_TYPES = (
    'employee',
    'contractor',
    'client_manager',
    'vendor_manager',
    'sales_rep',
    'executive_sponsor',
    'billing_contact',
    'support_contact',
    'debtor',
    'creditor',
    'other'
)


class ContactCompanyRelationship(Base):
    __tablename__ = "contact_company_relationship"
    __table_args__ = (
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_company_relationship_contact_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_contact_company_relationship_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="ck_contact_company_relationship_dates",
        ),
        CheckConstraint(
            f"relationship_type IN ({', '.join([repr(v) for v in _ALLOWED_CONTACT_COMPANY_TYPES])})",
            name="ck_contact_company_relationship_type",
        ),
        Index("ix_contact_company_relationship_tenant_contact", "tenant_id", "contact_id"),
        Index("ix_contact_company_relationship_tenant_company", "tenant_id", "company_id"),
        Index(
            "ux_contact_company_relationship_primary_per_contact",
            "tenant_id",
            "contact_id",
            unique=True,
            postgresql_where=text("is_primary IS TRUE"),
        ),
        Index(
            "ux_contact_company_relationship_unique",
            "tenant_id",
            "contact_id",
            "company_id",
            "relationship_type",
            unique=True,
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    contact_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)

    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    work_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_phone_raw: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    work_phone_e164: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    work_phone_ext: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    start_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Uses backref so you don't have to modify existing Contact/Company models for reverse navigation.
    contact: Mapped["Contact"] = relationship("Contact", backref="company_relationships")
    company: Mapped["Company"] = relationship("Company", backref="contact_relationships")

    def __repr__(self) -> str:
        return (
            f"<ContactCompanyRelationship id={self.id} tenant_id={self.tenant_id} "
            f"contact_id={self.contact_id} company_id={self.company_id} type={self.relationship_type}>"
        )
