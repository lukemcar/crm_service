"""
SQLAlchemy model for the TenantUserShadow projection.

This model mirrors the ``tenant_user_shadow`` table defined in the
support domain Liquibase changeset.  It stores a read‑only projection of
users from the tenant management service.  The table is tenant scoped
via the composite primary key (tenant_id, user_id) and includes basic
display attributes for convenience.  CRM does not modify rows in this
table directly; updates arrive via tenant service events.

The model intentionally follows existing ORM patterns in the CRM
codebase: explicit indexes matching the Liquibase DDL, audit
timestamps populated by the database, and a schema qualification on
``dyno_crm``.  Only the fields exposed in the DDL are represented
here; no additional convenience properties are added to keep the
projection minimal.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TenantUserShadow(Base):
    """ORM model for the ``tenant_user_shadow`` table.

    The table stores a projection of tenant users including their
    identifiers, display name and email.  Each row is uniquely
    identified by the composite primary key (tenant_id, user_id).  The
    ``is_active`` flag is used to indicate whether the user is active in
    the tenant service.  Timestamp fields mirror the DDL defaults and
    are managed by the database.  Partial indexes are defined to
    optimise lookups by tenant and email.
    """

    __tablename__ = "tenant_user_shadow"
    __table_args__ = (
        # Index for fast tenant‑scoped queries
        Index(
            "ix_tenant_user_shadow_tenant", "tenant_id"
        ),
        # Partial index on lower(email) for case‑insensitive email search
        Index(
            "ix_tenant_user_shadow_tenant_email",
            "tenant_id",
            text("lower(email)"),
            postgresql_where=text("email IS NOT NULL"),
        ),
        {
            "schema": "dyno_crm",
        },
    )

    # Composite primary key
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)

    # User display attributes
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Audit timestamps (managed by DB defaults and triggers)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<TenantUserShadow tenant_id={self.tenant_id} user_id={self.user_id} "
            f"display_name={self.display_name!r} email={self.email!r}>"
        )
