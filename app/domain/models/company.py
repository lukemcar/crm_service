"""SQLAlchemy model for Company (dyno_crm.company).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    text,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Company(Base):
    __tablename__ = "company"
    __table_args__ = (
        # Unique constraint on composite key (id, tenant_id)
        UniqueConstraint("id", "tenant_id", name="ux_company_id_tenant"),
        # Unique constraint on company name per tenant
        Index("ux_company_tenant_company_name", "tenant_id", "company_name", unique=True),
        # Standard tenant‑scoped indexes
        Index("ix_company_tenant", "tenant_id"),
        Index("ix_company_tenant_name", "tenant_id", "company_name"),
        # Domain index for case‑insensitive searches
        Index(
            "ix_company_tenant_domain",
            "tenant_id",
            text("lower(domain)"),
            postgresql_where=text("domain IS NOT NULL"),
        ),
        # Indexes for ownership fields to accelerate lookups
        Index("ix_company_tenant_owned_by_user", "tenant_id", "owned_by_user_id"),
        Index("ix_company_tenant_owned_by_group", "tenant_id", "owned_by_group_id"),
        # Composite foreign keys linking ownership fields to tenant projection tables
        ForeignKeyConstraint(
            ["tenant_id", "owned_by_user_id"],
            ["tenant_user_shadow.tenant_id", "tenant_user_shadow.user_id"],
            ondelete="SET NULL",
            name="fk_company_owned_by_user_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "owned_by_group_id"],
            ["tenant_group_shadow.tenant_id", "tenant_group_shadow.id"],
            ondelete="SET NULL",
            name="fk_company_owned_by_group_tenant",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -----------------------------------------------------------------
    # Ownership fields
    #
    # A company may be owned by a specific user or group.  Ownership
    # information is stored via UUIDs pointing to the tenant_user_shadow
    # and tenant_group_shadow projections.  These fields are optional and
    # default to NULL when not supplied.  Indexes and foreign key
    # constraints are defined in ``__table_args__`` above.
    # -----------------------------------------------------------------
    owned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    owned_by_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # -----------------------------------------------------------------
    # Child collections
    #
    # The schema uses BOTH:
    #   - FK(company_id) -> company(id)
    #   - FK(company_id, tenant_id) -> company(id, tenant_id)
    #
    # Explicit primaryjoin + foreign_keys avoids AmbiguousForeignKeysError.
    # -----------------------------------------------------------------

    emails: Mapped[List["CompanyEmail"]] = relationship(
        "CompanyEmail",
        primaryjoin="and_(Company.id==CompanyEmail.company_id, Company.tenant_id==CompanyEmail.tenant_id)",
        foreign_keys="(CompanyEmail.company_id, CompanyEmail.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    phones: Mapped[List["CompanyPhone"]] = relationship(
        "CompanyPhone",
        primaryjoin="and_(Company.id==CompanyPhone.company_id, Company.tenant_id==CompanyPhone.tenant_id)",
        foreign_keys="(CompanyPhone.company_id, CompanyPhone.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    addresses: Mapped[List["CompanyAddress"]] = relationship(
        "CompanyAddress",
        primaryjoin="and_(Company.id==CompanyAddress.company_id, Company.tenant_id==CompanyAddress.tenant_id)",
        foreign_keys="(CompanyAddress.company_id, CompanyAddress.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    social_profiles: Mapped[List["CompanySocialProfile"]] = relationship(
        "CompanySocialProfile",
        primaryjoin="and_(Company.id==CompanySocialProfile.company_id, Company.tenant_id==CompanySocialProfile.tenant_id)",
        foreign_keys="(CompanySocialProfile.company_id, CompanySocialProfile.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
    )

    notes: Mapped[List["CompanyNote"]] = relationship(
        "CompanyNote",
        primaryjoin="and_(Company.id==CompanyNote.company_id, Company.tenant_id==CompanyNote.tenant_id)",
        foreign_keys="(CompanyNote.company_id, CompanyNote.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="company",
        order_by="desc(CompanyNote.noted_at)",
    )

    # Company-to-company relationships (directional)
    relationships_from: Mapped[List["CompanyRelationship"]] = relationship(
        "CompanyRelationship",
        primaryjoin="and_(Company.id==CompanyRelationship.from_company_id, Company.tenant_id==CompanyRelationship.tenant_id)",
        foreign_keys="(CompanyRelationship.from_company_id, CompanyRelationship.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="from_company",
        overlaps="relationships_to",
    )

    relationships_to: Mapped[List["CompanyRelationship"]] = relationship(
        "CompanyRelationship",
        primaryjoin="and_(Company.id==CompanyRelationship.to_company_id, Company.tenant_id==CompanyRelationship.tenant_id)",
        foreign_keys="(CompanyRelationship.to_company_id, CompanyRelationship.tenant_id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="to_company",
        overlaps="relationships_from",
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} tenant_id={self.tenant_id} name={self.company_name}>"

    # -----------------------------------------------------------------
    # Convenience properties
    # -----------------------------------------------------------------
    @property
    def name(self) -> str:
        return self.company_name

    @name.setter
    def name(self, value: str) -> None:
        self.company_name = value

    @property
    def website(self) -> Optional[str]:
        return self.domain

    @website.setter
    def website(self, value: Optional[str]) -> None:
        self.domain = value
