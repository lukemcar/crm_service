# app/models/company_social_profile.py
"""SQLAlchemy model for CompanySocialProfile (dyno_crm.company_social_profile).

DDL is the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


_ALLOWED_PROFILE_TYPES = (
    'facebook','instagram','tiktok','snapchat','x','twitter','threads','bluesky','mastodon','reddit',
    'pinterest','tumblr','discord','telegram','whatsapp','signal','wechat','line','kakaotalk','viber','skype',
    'linkedin','github','gitlab','bitbucket','stack_overflow','medium','substack','devto','hashnode',
    'behance','dribbble','figma_community','product_hunt',
    'youtube','twitch','kick','vimeo','rumble','dailymotion',
    'spotify','soundcloud','bandcamp','apple_music',
    'etsy','ebay','amazon_storefront','shopify_store','depop','poshmark','mercari',
    'google_business_profile','yelp','tripadvisor','trustpilot','angies_list','bbb',
    'website','blog','portfolio','calendly','linktree','patreon','onlyfans','other'
)


class CompanySocialProfile(Base):
    __tablename__ = "company_social_profile"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "tenant_id"],
            ["dyno_crm.company.id", "dyno_crm.company.tenant_id"],
            name="fk_company_social_profile_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "profile_url ~* '^https?://'",
            name="ck_company_social_profile_url",
        ),
        CheckConstraint(
            f"profile_type IN ({', '.join([repr(v) for v in _ALLOWED_PROFILE_TYPES])})",
            name="ck_company_social_profile_profile_type",
        ),
        Index("ix_company_social_profile_tenant_company", "tenant_id", "company_id"),
        Index(
            "ux_company_social_profile_company_type",
            "tenant_id",
            "company_id",
            text("lower(profile_type)"),
            unique=True,
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

    profile_type: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company: Mapped["Company"] = relationship(
        "Company",
        primaryjoin="and_(Company.id==CompanySocialProfile.company_id, Company.tenant_id==CompanySocialProfile.tenant_id)",
        foreign_keys="(CompanySocialProfile.company_id, CompanySocialProfile.tenant_id)",
        back_populates="social_profiles",
    )

    def __repr__(self) -> str:
        return f"<CompanySocialProfile id={self.id} tenant_id={self.tenant_id} company_id={self.company_id} type={self.profile_type}>"
