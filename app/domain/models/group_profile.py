"""
SQLAlchemy model for the GroupProfile entity.

This model represents CRM-local metadata describing how a mirrored group
from the tenant service behaves within the support module.  It stores
support queue flags, default SLA policies, routing configuration for
work distribution and AI posture defaults.  Group profiles are scoped
by tenant and refer back to the underlying ``tenant_group_shadow`` via
foreign keys.  Uniqueness constraints ensure that at most one profile
exists per (tenant_id, group_id).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
    CheckConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class GroupProfile(Base):
    """ORM model for the ``group_profile`` table."""

    __tablename__ = "group_profile"
    __table_args__ = (
        # Unique constraints
        UniqueConstraint("id", "tenant_id", name="ux_group_profile_id_tenant"),
        UniqueConstraint("tenant_id", "group_id", name="ux_group_profile_unique_by_group"),
        # Indexes to accelerate queries
        Index("ix_group_profile_tenant_type", "tenant_id", "profile_type"),
        Index(
            "ix_group_profile_tenant_support_queue",
            "tenant_id",
            "is_support_queue",
            postgresql_where=text("is_support_queue = TRUE"),
        ),
        # Check constraints for enumerated fields
        CheckConstraint(
            "profile_type IN ('support_queue','sales_team','security_only','generic')",
            name="ck_group_profile_type",
        ),
        CheckConstraint(
            "ai_work_mode_default IN ('human_only','ai_allowed','ai_preferred','ai_only')",
            name="ck_group_profile_ai_work_mode_default",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    group_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.tenant_group_shadow.id", ondelete="CASCADE"),
        nullable=False,
    )

    profile_type: Mapped[str] = mapped_column(String(50), nullable=False, default="support_queue")
    is_support_queue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_assignable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    default_sla_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.sla_policy.id", ondelete="SET NULL"),
        nullable=True,
    )
    routing_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ai_work_mode_default: Mapped[str] = mapped_column(String(50), nullable=False, default="human_only")
    business_hours_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<GroupProfile id={self.id} tenant_id={self.tenant_id} group_id={self.group_id} "
            f"profile_type={self.profile_type} is_support_queue={self.is_support_queue}>"
        )
