"""
SQLAlchemy model for SupportMacro (dyno_crm.support_macro).

Macros represent one‑click actions that agents can apply to tickets.
Each macro stores a name, description, activation status and a JSON
array of actions.  Actions are interpreted by application logic to
update tickets (e.g. set status, assign to queue, add reply).  All
macros are tenant scoped and include audit fields.  See the DDL in
``002_support_domain_schema.sql`` for the complete definition.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

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


class SupportMacro(Base):
    """SQLAlchemy model for the support_macro table.

    Macros store reusable actions that agents can apply to tickets with
    a single click.  The ``actions`` column contains a JSON array of
    operations to execute (e.g. set status, add tags, assign).  Macros
    are tenant scoped and may be activated or deactivated.  Audit
    fields track who created and last updated the macro.
    """

    __tablename__ = "support_macro"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_support_macro_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_support_macro_tenant_name"),
        Index("ix_support_macro_tenant", "tenant_id"),
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
        doc="Name of the macro",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional description of the macro",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    actions: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        doc="JSON array of operations comprising the macro",
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
            f"<SupportMacro id={self.id} tenant_id={self.tenant_id} name={self.name}>"
        )


__all__ = ["SupportMacro"]