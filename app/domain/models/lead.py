"""SQLAlchemy model for Lead.

Loose lead model intended for sparse intake data. lead_data is JSONB and is
validated at the DB level via chk_lead_lead_data_schema, and at the API level
via Pydantic models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Lead(Base):
    __tablename__ = "lead"
    __table_args__ = (
        # Existing indexes on tenant and name for search
        Index("ix_lead_tenant", "tenant_id"),
        Index("ix_lead_tenant_last_first", "tenant_id", "last_name", "first_name"),
        # Indexes for ownership fields to accelerate lookups
        Index("ix_lead_tenant_owned_by_user", "tenant_id", "owned_by_user_id"),
        Index("ix_lead_tenant_owned_by_group", "tenant_id", "owned_by_group_id"),
        # Composite foreign keys linking ownership fields to tenant projection tables
        ForeignKeyConstraint(
            ["tenant_id", "owned_by_user_id"],
            ["tenant_user_shadow.tenant_id", "tenant_user_shadow.user_id"],
            ondelete="SET NULL",
            name="fk_lead_owned_by_user_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "owned_by_group_id"],
            ["tenant_group_shadow.tenant_id", "tenant_group_shadow.id"],
            ondelete="SET NULL",
            name="fk_lead_owned_by_group_tenant",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # lead_data schema enforced by DB CHECK + API Pydantic model
    lead_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # -----------------------------------------------------------------
    # Ownership fields
    #
    # A lead may be owned by a specific user or group.  Ownership
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

    def __repr__(self) -> str:
        return f"<Lead id={self.id} tenant_id={self.tenant_id} name={self.last_name},{self.first_name}>"
