"""SQLAlchemy model for InboundChannel (dyno_crm.inbound_channel).

This model represents inbound communication channels through which
customers can create or update tickets (e.g. email inboxes, chat
widgets, SMS numbers).  Each channel is scoped to a tenant and
optionally includes a provider reference (external_ref) and JSON
configuration.  Only non‑secret information should be stored in this
table.  Secrets belong in integration services or a secrets manager.

The DDL defined in ``002_support_domain_schema.sql`` is the source of
truth.  Constraints and indexes mirror those definitions here.
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


class InboundChannel(Base):
    """SQLAlchemy model for the inbound_channel table.

    The table resides in the ``dyno_crm`` schema and enforces tenant
    scoping on all records.  Channels may be configured for email, web
    forms, chat, SMS, voice, API, internal or social channels.  See
    the check constraint on ``channel_type`` for allowed values.
    """

    __tablename__ = "inbound_channel"
    __table_args__ = (
        # Unique constraints
        UniqueConstraint("id", "tenant_id", name="ux_inbound_channel_id_tenant"),
        # Channel type enumeration
        CheckConstraint(
            "channel_type IN ('email','web','chat','sms','voice','api','internal','social')",
            name="ck_inbound_channel_type",
        ),
        # Index to accelerate tenant lookups
        Index("ix_inbound_channel_tenant", "tenant_id"),
        # Unique index on (tenant_id, channel_type, external_ref) when external_ref is not null
        Index(
            "ux_inbound_channel_tenant_external_ref",
            "tenant_id",
            "channel_type",
            "external_ref",
            unique=True,
            postgresql_where=text("external_ref IS NOT NULL"),
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

    channel_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of channel (email, web, chat, sms, voice, api, internal, social)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Friendly label for the inbound channel",
    )
    external_ref: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Provider identifier such as mailbox ID or phone number ID",
    )
    # Use JSON type to store arbitrary config; Postgres stores as JSONB automatically.
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Non‑secret provider configuration encoded as JSON",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
            f"<InboundChannel id={self.id} tenant_id={self.tenant_id} "
            f"type={self.channel_type} name={self.name}>"
        )


__all__ = ["InboundChannel"]