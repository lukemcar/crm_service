"""
SQLAlchemy model for SupportView (dyno_crm.support_view).

This model represents saved ticket list views in the support module.  A
support view stores filter and sort definitions that agents can use to
quickly load commonly used queues such as "My Open Tickets" or "High
Priority Incidents".  Views are tenant scoped and include audit
information for tracking creation and updates.  See the DDL in
``002_support_domain_schema.sql`` for the authoritative schema.  This
model mirrors the DDL with appropriate constraints and indexes.
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


class SupportView(Base):
    """SQLAlchemy model for the support_view table.

    Each support view defines a set of filters and sort orders for
    tickets.  Views are read and written by users to persist their
    preferred ways of looking at tickets.  The filter_definition
    column must always be provided and contains a JSON object
    describing the query parameters to apply when fetching tickets.
    Sort definitions are optional and also encoded as JSON.  Audit
    fields track who created or updated the view.  All records are
    scoped to a tenant via the ``tenant_id`` column.
    """

    __tablename__ = "support_view"
    __table_args__ = (
        # Unique constraints to enforce tenant scoping
        UniqueConstraint("id", "tenant_id", name="ux_support_view_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_support_view_tenant_name"),
        # Index on tenant_id for efficient listing
        Index("ix_support_view_tenant", "tenant_id"),
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
        doc="Name of the saved view",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional description of the view",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # JSON definitions for filters and sorts; filter_definition is required
    filter_definition: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="JSON object encoding filter criteria for the view",
    )
    sort_definition: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Optional JSON object encoding sort preferences",
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
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial repr
        return (
            f"<SupportView id={self.id} tenant_id={self.tenant_id} name={self.name}>"
        )


__all__ = ["SupportView"]