"""SQLAlchemy model for List (Segment).

Represents a saved segment of CRM records. Lists are tenant scoped and
support static and snapshot types. Memberships are stored in the
ListMembership table.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List as TList, Optional

from sqlalchemy import DateTime, Index, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class List(Base):
    __tablename__ = "lists"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "object_type", name="ux_lists_tenant_name_object"),
        Index("ix_lists_tenant", "tenant_id"),
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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    object_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    list_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    filter_definition: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

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

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    memberships: Mapped[TList["ListMembership"]] = relationship(
        "ListMembership",
        back_populates="list",
        cascade="all, delete-orphan",
        passive_deletes=True,  # DB handles cascade via ON DELETE CASCADE
    )

    def __repr__(self) -> str:
        return f"<List id={self.id} name={self.name} type={self.list_type}>"
