"""
SQLAlchemy model for SLA Policy.

This model represents a Service Level Agreement (SLA) definition that can
be applied to tickets.  An SLA policy belongs to a tenant and defines
matching rules in the ``match_rules`` JSON document.  Policies can be
activated or deactivated without being deleted.  Each policy may have
one or more associated targets that specify deadlines for different
ticket priorities (low/normal/high/urgent).  Policies support full
CRUD operations via the API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SlaPolicy(Base):
    """ORM model for the ``sla_policy`` table."""

    __tablename__ = "sla_policy"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_sla_policy_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_sla_policy_tenant_name"),
        Index("ix_sla_policy_tenant", "tenant_id"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Optional JSON rules used to match tickets to this SLA policy.  The exact
    # schema is application-defined and may include channel, priority, or
    # customer segment criteria.  Stored as JSON for flexibility.
    match_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<SlaPolicy id={self.id} tenant_id={self.tenant_id} name={self.name}>"
