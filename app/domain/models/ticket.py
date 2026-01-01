"""
SQLAlchemy model for the Ticket entity (dyno_crm.ticket).

This model represents the durable unit of work for customer support
cases.  Tickets capture high‑level properties of a request,
assignment targets, timestamps, custom fields, orchestration and AI
pointers.  The DDL defined in the support domain schema is the
source of truth; constraints and indexes here mirror that definition.
Nested resources such as messages, participants, tags and audits
are defined in separate tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
    JSON,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Ticket(Base):
    """ORM model for the ``ticket`` table."""

    __tablename__ = "ticket"
    __table_args__ = (
        # Unique constraint on (id, tenant_id)
        UniqueConstraint("id", "tenant_id", name="ux_ticket_id_tenant"),
        # Check constraints for enumerated fields
        CheckConstraint(
            "status IN ('new','open','pending','on_hold','solved','closed')",
            name="ck_ticket_status",
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','urgent')",
            name="ck_ticket_priority",
        ),
        CheckConstraint(
            "ticket_type IN ('question','incident','problem','task')",
            name="ck_ticket_type",
        ),
        CheckConstraint(
            "work_mode IN ('human_only','ai_allowed','ai_preferred','ai_only')",
            name="ck_ticket_work_mode",
        ),
        CheckConstraint(
            "ai_status IN ('idle','queued','working','waiting_for_human','blocked','completed','failed')",
            name="ck_ticket_ai_status",
        ),
        CheckConstraint(
            "ai_last_outcome IS NULL OR ai_last_outcome IN ('success','partial','failed','canceled')",
            name="ck_ticket_ai_outcome",
        ),
        # Indexes for common queries
        Index("ix_ticket_tenant", "tenant_id"),
        Index("ix_ticket_tenant_status", "tenant_id", "status"),
        Index("ix_ticket_tenant_priority", "tenant_id", "priority"),
        Index(
            "ix_ticket_tenant_assigned_user",
            "tenant_id",
            "assigned_user_id",
            postgresql_where=text("assigned_user_id IS NOT NULL"),
        ),
        Index(
            "ix_ticket_tenant_assigned_group",
            "tenant_id",
            "assigned_group_id",
            postgresql_where=text("assigned_group_id IS NOT NULL"),
        ),
        Index(
            "ix_ticket_tenant_last_message",
            "tenant_id",
            "last_message_at",
            postgresql_where=text("last_message_at IS NOT NULL"),
            postgresql_using="btree",
        ),
        Index(
            "ix_ticket_tenant_ai_status",
            "tenant_id",
            "ai_status",
        ),
        {"schema": "dyno_crm"},
    )

    # Primary key and tenant scope
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # Customer context
    requester_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dyno_crm.contact.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dyno_crm.company.id", ondelete="SET NULL"), nullable=True
    )

    # Channel / entry point
    inbound_channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dyno_crm.inbound_channel.id", ondelete="SET NULL"), nullable=True
    )

    # Optional form selection for custom fields
    ticket_form_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dyno_crm.ticket_form.id", ondelete="SET NULL"), nullable=True
    )

    # Basic properties
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    ticket_type: Mapped[str] = mapped_column(String(50), nullable=False, default="question")

    # Assignment targets
    assigned_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("dyno_crm.tenant_group_shadow.id", ondelete="SET NULL"), nullable=True
    )
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Timestamps
    first_response_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Custom fields
    custom_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Orchestration linkage
    orchestration_workflow_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    orchestration_instance_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    orchestration_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # AI posture
    work_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="human_only")
    ai_status: Mapped[str] = mapped_column(String(50), nullable=False, default="idle")
    ai_last_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    ai_last_agent_key: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    ai_last_outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_last_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    ai_last_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Ticket id={self.id} tenant_id={self.tenant_id} subject={self.subject!r} "
            f"status={self.status} priority={self.priority}>"
        )


__all__ = ["Ticket"]