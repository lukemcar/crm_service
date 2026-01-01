"""
SQLAlchemy model for SLA Target.

An SLA target defines the specific response and resolution deadlines
applicable to tickets of a given priority under an SLA policy.  Each
target belongs to a tenant and references a parent ``sla_policy``.  A
policy may include multiple targets, one per priority.  Targets are
managed via the API alongside their parent policies.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SlaTarget(Base):
    """ORM model for the ``sla_target`` table."""

    __tablename__ = "sla_target"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_sla_target_id_tenant"),
        UniqueConstraint(
            "tenant_id", "sla_policy_id", "priority", name="ux_sla_target_unique"
        ),
        ForeignKeyConstraint([
            "sla_policy_id"
        ], ["dyno_crm.sla_policy.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["sla_policy_id", "tenant_id"],
            ["dyno_crm.sla_policy.id", "dyno_crm.sla_policy.tenant_id"],
            ondelete="CASCADE",
        ),
        Index("ix_sla_target_tenant", "tenant_id"),
        CheckConstraint(
            "priority IN ('low','normal','high','urgent')", name="ck_sla_target_priority"
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )

    sla_policy_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    first_response_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    next_response_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SlaTarget id={self.id} tenant_id={self.tenant_id} "
            f"sla_policy_id={self.sla_policy_id} priority={self.priority}>"
        )
