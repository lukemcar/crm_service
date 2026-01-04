"""
SQLAlchemy model for record watcher.

This model represents subscriptions to record changes across the CRM.
A watcher identifies a record by its type and ID and associates it
with a principal (user or group) within a tenant.  The composite
primary key ensures that a principal can subscribe to a record only
once.  Indexes support efficient lookups by record or principal.

The underlying table is created via Liquibase (see consolidated
CRM change request) and lives in the ``dyno_crm`` schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RecordWatcher(Base):
    """SQLAlchemy model mapping to ``dyno_crm.record_watcher``.

    Each watcher links a tenant, record and principal.  The composite
    primary key spans all identifying columns; no surrogate ID is used.
    """

    __tablename__ = "record_watcher"
    __table_args__ = (
        # Index to quickly find watchers by principal
        Index(
            "ix_record_watcher_principal",
            "tenant_id",
            "principal_type",
            "principal_id",
        ),
        # Index to quickly find watchers by record
        Index(
            "ix_record_watcher_record",
            "tenant_id",
            "record_type",
            "record_id",
        ),
        {"schema": "dyno_crm"},
    )

    # Tenant identifier (part of composite PK)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, nullable=False
    )

    # Type of the record being watched (e.g. CONTACT, COMPANY, DEAL)
    record_type: Mapped[str] = mapped_column(
        String(50), primary_key=True, nullable=False
    )

    # Identifier of the record being watched
    record_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, nullable=False
    )

    # Type of the principal subscribing to the record (USER or GROUP)
    principal_type: Mapped[str] = mapped_column(
        String(20), primary_key=True, nullable=False
    )

    # Identifier of the subscribing principal
    principal_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, nullable=False
    )

    # Timestamp when the subscription was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # User ID of the creator (nullable for system subscriptions)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<RecordWatcher tenant={self.tenant_id} record={self.record_type}:{self.record_id} "
            f"principal={self.principal_type}:{self.principal_id}>"
        )
