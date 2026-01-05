"""
SQLAlchemy model for RecordWatcher.

This model represents a subscription to changes on a specific CRM record
by a principal (user or group).  It mirrors the list membership
patterns but uses a composite primary key rather than a surrogate ID.
Each watcher is uniquely identified by the combination of tenant,
record and principal identifiers.

Fields:

* ``tenant_id`` – UUID identifying the tenant that owns the watcher
* ``record_type`` – string indicating the type of the record (e.g. contact, company, deal)
* ``record_id`` – UUID of the record being watched
* ``principal_type`` – string indicating the type of principal subscribing (e.g. user, group)
* ``principal_id`` – UUID of the subscribing principal
* ``created_at`` – timestamp when the watcher was created
* ``created_by_user_id`` – identifier of the user who created the watcher (for audit)

Indexes are defined to support efficient queries by record and by principal.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RecordWatcher(Base):
    """SQLAlchemy model class for record watchers."""

    __tablename__ = "record_watchers"
    __table_args__ = (
        # Composite primary key ensures uniqueness across tenant/record/principal
        PrimaryKeyConstraint(
            "tenant_id",
            "record_type",
            "record_id",
            "principal_type",
            "principal_id",
            name="pk_record_watchers",
        ),
        # Index to efficiently list watchers for a record
        Index(
            "ix_record_watchers_record",
            "tenant_id",
            "record_type",
            "record_id",
        ),
        # Index to efficiently list watchers for a principal
        Index(
            "ix_record_watchers_principal",
            "tenant_id",
            "principal_type",
            "principal_id",
        ),
        {"schema": "dyno_crm"},
    )

    # Tenant identifier
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    # Record being watched
    record_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    record_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    # Principal subscribing to changes
    principal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    principal_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<RecordWatcher tenant={self.tenant_id} record={self.record_type}:{self.record_id} "
            f"principal={self.principal_type}:{self.principal_id}>"
        )