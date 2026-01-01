"""
SQLAlchemy model for the TenantGroupShadow projection.

This model mirrors the ``tenant_group_shadow`` table defined in the
support domain schema.  It provides a read‑only projection of groups
from the tenant management service, including optional group keys and
descriptive metadata.  CRM uses this projection to enforce tenant
constraints on ticket assignments and to display group names without
calling the tenant service on every request.

As with other models, indexes reflect those specified in the
Liquibase DDL.  The ``id`` column is the primary key while the
``ux_tenant_group_shadow_id_tenant`` constraint is implemented via a
unique index on (id, tenant_id).  Partial indexes accelerate lookups
by group key when present.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TenantGroupShadow(Base):
    """ORM model for the ``tenant_group_shadow`` table.

    The table stores a projection of tenant groups.  Groups are
    identified by a stable UUID (``id``) and scoped by ``tenant_id``.
    Descriptive fields such as ``group_name``, ``group_key`` and
    ``description`` provide context for the UI and integration layers.
    The ``is_active`` flag mirrors the active state in the tenant
    service.  Unique constraints and indexes mirror the Liquibase
    definitions.
    """

    __tablename__ = "tenant_group_shadow"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_tenant_group_shadow_id_tenant"),
        Index(
            "ux_tenant_group_shadow_tenant_name", "tenant_id", "group_name", unique=True
        ),
        Index("ix_tenant_group_shadow_tenant", "tenant_id"),
        Index(
            "ix_tenant_group_shadow_tenant_group_key",
            "tenant_id",
            "group_key",
            postgresql_where=text("group_key IS NOT NULL"),
        ),
        {
            "schema": "dyno_crm",
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<TenantGroupShadow id={self.id} tenant_id={self.tenant_id} "
            f"group_name={self.group_name!r}>"
        )
