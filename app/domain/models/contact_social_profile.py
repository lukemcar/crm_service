# app/models/contact_social_profile.py
"""SQLAlchemy model for ContactSocialProfile.

Schema: dyno_crm.contact_social_profile
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


_ALLOWED_PROFILE_TYPES = (
    "facebook",
    "instagram",
    "tiktok",
    "snapchat",
    "x",
    "twitter",
    "threads",
    "bluesky",
    "mastodon",
    "reddit",
    "pinterest",
    "tumblr",
    "discord",
    "telegram",
    "whatsapp",
    "signal",
    "wechat",
    "line",
    "kakaotalk",
    "viber",
    "skype",
    "linkedin",
    "github",
    "gitlab",
    "bitbucket",
    "stack_overflow",
    "medium",
    "substack",
    "devto",
    "hashnode",
    "behance",
    "dribbble",
    "figma_community",
    "product_hunt",
    "youtube",
    "twitch",
    "kick",
    "vimeo",
    "rumble",
    "dailymotion",
    "spotify",
    "soundcloud",
    "bandcamp",
    "apple_music",
    "etsy",
    "ebay",
    "amazon_storefront",
    "shopify_store",
    "depop",
    "poshmark",
    "mercari",
    "google_business_profile",
    "yelp",
    "tripadvisor",
    "trustpilot",
    "angies_list",
    "bbb",
    "website",
    "blog",
    "portfolio",
    "calendly",
    "linktree",
    "patreon",
    "onlyfans",
    "other",
)


class ContactSocialProfile(Base):
    __tablename__ = "contact_social_profile"
    __table_args__ = (
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["dyno_crm.contact.id", "dyno_crm.contact.tenant_id"],
            name="fk_contact_social_profile_contact_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "profile_url ~* '^https?://'",
            name="ck_contact_social_profile_url",
        ),
        CheckConstraint(
            f"profile_type IN ({', '.join([repr(v) for v in _ALLOWED_PROFILE_TYPES])})",
            name="ck_contact_social_profile_profile_type",
        ),
        Index("ix_contact_social_profile_tenant_contact", "tenant_id", "contact_id"),
        Index(
            "ux_contact_social_profile_contact_type",
            "tenant_id",
            "contact_id",
            func.lower("profile_type"),
            unique=True,
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.contact.id", ondelete="CASCADE"),
        nullable=False,
    )

    profile_type: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="social_profiles")

    def __repr__(self) -> str:
        return f"<ContactSocialProfile id={self.id} tenant_id={self.tenant_id} contact_id={self.contact_id} type={self.profile_type}>"
