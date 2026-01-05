"""SQLAlchemy model for List (Segment).

Represents a saved segment of CRM records. Lists are tenant scoped and
support static and snapshot types. Memberships are stored in the
ListMembership table.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List as TList, Optional

from sqlalchemy import DateTime, Index, JSON, String, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class List(Base):
    __tablename__ = "lists"
    __table_args__ = (
        # Each list name must be unique per tenant and object type
        UniqueConstraint("tenant_id", "name", "object_type", name="ux_lists_tenant_name_object"),
        # Index on tenant to support tenant scoped queries
        Index("ix_lists_tenant", "tenant_id"),
        # Additional index on (tenant_id, object_type) to support filtering by object_type
        Index("ix_lists_tenant_object_type", "tenant_id", "object_type"),
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

    # New fields introduced in the consolidated change request
    # processing_type denotes how the list should be processed.  It mirrors
    # the ``list_processing_type`` Postgres enum but is stored as a string
    # here.  Default is "STATIC" for backward compatibility.
    processing_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STATIC",
    )

    # is_archived indicates whether the list has been archived.  Archived
    # lists remain in the database but should be excluded from normal
    # processing.  Default is False.
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    memberships: Mapped[TList["ListMembership"]] = relationship(
        "ListMembership",
        back_populates="list",
        cascade="all, delete-orphan",
        passive_deletes=True,  # DB handles cascade via ON DELETE CASCADE
    )

    def __repr__(self) -> str:
        return f"<List id={self.id} name={self.name} type={self.list_type}>"
