"""
SQLAlchemy model for TicketFieldDef (dyno_crm.ticket_field_def).

This model represents definitions of custom fields that can be attached
to tickets via forms.  Field definitions are scoped to a tenant and
include a unique key, human‑friendly label, data type, optional
validation rules and UI configuration.  The database enforces
uniqueness of the ``field_key`` per tenant and restricts the
``field_type`` to supported values via a check constraint.  Fields can
be marked required or inactive.  The DDL defined in
``002_support_domain_schema.sql`` is the source of truth; this model
mirrors those constraints and indexes.
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
    CheckConstraint,
    text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TicketFieldDef(Base):
    """SQLAlchemy model for the ``ticket_field_def`` table.

    Custom field definitions allow tenants to define structured data
    types beyond the built‑in ticket attributes.  Each definition
    includes a stable ``field_key`` used for storing values and a
    ``label`` used for display.  Supported field types include simple
    primitives and select/multiselect enumerations.  Validation and
    UI configuration are stored as JSON for flexibility.  The
    ``is_required`` flag indicates whether the field must be provided
    when present on a form, and ``is_active`` allows definitions to
    be deactivated without deletion.
    """

    __tablename__ = "ticket_field_def"
    __table_args__ = (
        # Enforce unique id per tenant
        UniqueConstraint("id", "tenant_id", name="ux_ticket_field_def_id_tenant"),
        # Enforce allowed field types
        CheckConstraint(
            "field_type IN ('text','textarea','number','boolean','date','datetime','select','multiselect')",
            name="ck_ticket_field_def_type",
        ),
        # Unique key per tenant (case-insensitive)
        Index(
            "ux_ticket_field_def_tenant_key",
            "tenant_id",
            text("lower(field_key)"),
            unique=True,
        ),
        # Index to accelerate tenant lookups
        Index("ix_ticket_field_def_tenant", "tenant_id"),
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

    field_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Stable key for the custom field (unique per tenant)",
    )
    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human‑friendly label for the field",
    )
    field_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of the field (text, textarea, number, boolean, date, datetime, select, multiselect)",
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether the field must be provided when part of a form",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether the field definition is active",
    )
    validation: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Optional JSON schema or rules for validation of the field value",
    )
    ui_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Optional UI configuration for rendering this field",
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
            f"<TicketFieldDef id={self.id} tenant_id={self.tenant_id} "
            f"field_key={self.field_key} field_type={self.field_type}>"
        )


__all__ = ["TicketFieldDef"]