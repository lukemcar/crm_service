"""
SQLAlchemy model for the ticket_task_mirror table.

This table mirrors work tasks created by the orchestration service (e.g., Flowable) for
support tickets. It allows the CRM UI to display and filter tasks without
directly querying the orchestration engine. Records in this table are
typically created and updated by asynchronous listeners consuming
orchestration events. Tenants can only read these records; updates
are performed via admin/internal APIs to support recovery or backfill.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    ForeignKey,
    Index,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class TicketTaskMirror(Base):
    """SQLAlchemy model for the ``ticket_task_mirror`` table."""

    __tablename__ = "ticket_task_mirror"
    __table_args__ = (
        # Ensure uniqueness of id per tenant
        UniqueConstraint("id", "tenant_id", name="ux_ticket_task_mirror_id_tenant"),
        # Unique orchestration_task_id per tenant to prevent duplicates
        UniqueConstraint(
            "tenant_id",
            "orchestration_task_id",
            name="ux_ticket_task_mirror_unique",
        ),
        # Foreign key to ticket with tenant scoping
        ForeignKeyConstraint([
            "ticket_id",
        ], ["dyno_crm.ticket.id"], name="fk_ticket_task_mirror_ticket", ondelete="CASCADE"),
        ForeignKeyConstraint([
            "ticket_id",
            "tenant_id",
        ], ["dyno_crm.ticket.id", "dyno_crm.ticket.tenant_id"], name="fk_ticket_task_mirror_ticket_tenant", ondelete="CASCADE"),
        # FK to assigned user projection
        ForeignKeyConstraint([
            "tenant_id",
            "assigned_user_id",
        ], ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
        name="fk_ticket_task_mirror_assigned_user_tenant", ondelete="SET NULL"),
        # FK to assigned group projection
        ForeignKeyConstraint([
            "assigned_group_id",
            "tenant_id",
        ], ["dyno_crm.tenant_group_shadow.id", "dyno_crm.tenant_group_shadow.tenant_id"],
        name="fk_ticket_task_mirror_assigned_group_tenant", ondelete="SET NULL"),
        # Indexes to support querying by tenant and ticket
        Index(
            "ix_ticket_task_mirror_tenant_ticket",
            "tenant_id",
            "ticket_id",
        ),
        Index(
            "ix_ticket_task_mirror_tenant_status",
            "tenant_id",
            "status",
        ),
        {
            "schema": "dyno_crm",
        },
    )

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    # Tenant that owns this record
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)

    # Ticket foreign key
    ticket_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)

    # Identifiers from orchestration service
    orchestration_task_id: str = Column(String(128), nullable=False)
    orchestration_process_instance_id: Optional[str] = Column(String(128))
    orchestration_process_definition_key: Optional[str] = Column(String(255))

    # Task metadata
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(String)

    # Status of the task: open, completed or canceled
    status: str = Column(String(50), nullable=False, default="open")
    due_at: Optional[datetime] = Column(DateTime(timezone=True))

    # Assignment info (nullable)
    assigned_user_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True))
    assigned_group_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True))

    # Audit fields
    created_at: datetime = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<TicketTaskMirror id={self.id} ticket_id={self.ticket_id} "
            f"task_id={self.orchestration_task_id} tenant_id={self.tenant_id}>"
        )


__all__ = ["TicketTaskMirror"]