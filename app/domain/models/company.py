# app/models/company.py
"""SQLAlchemy model for Company (dyno_crm.company).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Company(Base):
    __tablename__ = "company"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_company_id_tenant"),
        Index("ux_company_tenant_company_name", "tenant_id", "company_name", unique=True),
        Index("ix_company_tenant", "tenant_id"),
        Index("ix_company_tenant_name", "tenant_id", "company_name"),
        Index(
            "ix_company_tenant_domain",
            "tenant_id",
            func.lower("domain"),
            postgresql_where=text("domain IS NOT NULL"),
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    emails: Mapped[List["CompanyEmail"]] = relationship(
        "CompanyEmail",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    phones: Mapped[List["CompanyPhone"]] = relationship(
        "CompanyPhone",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    addresses: Mapped[List["CompanyAddress"]] = relationship(
        "CompanyAddress",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    social_profiles: Mapped[List["CompanySocialProfile"]] = relationship(
        "CompanySocialProfile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    notes: Mapped[List["CompanyNote"]] = relationship(
        "CompanyNote",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
        order_by="desc(CompanyNote.noted_at)",
    )

    # Company-to-company relationships (directional)
    relationships_from: Mapped[List["CompanyRelationship"]] = relationship(
        "CompanyRelationship",
        foreign_keys="CompanyRelationship.from_company_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="from_company",
    )
    relationships_to: Mapped[List["CompanyRelationship"]] = relationship(
        "CompanyRelationship",
        foreign_keys="CompanyRelationship.to_company_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="to_company",
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} tenant_id={self.tenant_id} name={self.company_name}>"

    # -----------------------------------------------------------------
    # Convenience properties
    # -----------------------------------------------------------------
    @property
    def name(self) -> str:
        """Alias for the company name used by Pydantic schemas.

        The external API refers to the company name as ``name``.  The
        underlying database column is ``company_name``.  Expose a
        read/write alias so that response models can access the name
        attribute via ``from_attributes=True``.
        """
        return self.company_name

    @name.setter
    def name(self, value: str) -> None:
        self.company_name = value

    @property
    def website(self) -> Optional[str]:
        """Alias for the company website/domain used by Pydantic schemas.

        The API refers to the domain as ``website`` to align with
        user terminology.  The underlying column is ``domain``.  This
        property exposes a read/write alias.
        """
        return self.domain

    @website.setter
    def website(self, value: Optional[str]) -> None:
        self.domain = value
