"""
SQLAlchemy model for AutomationActionExecution.

This model captures the execution logs for automation actions.  Each execution
record stores the entity context, status transitions and any response or
error information returned by downstream systems.  A unique constraint
enforces one execution per tenant and execution_key, and composite foreign
keys reference the parent automation action.  Indexes support efficient
queries by action and status or by entity context【480489992503603†L343-L367】.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Index,
    UniqueConstraint,
    ForeignKeyConstraint,
    String,
    Integer,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AutomationActionExecution(Base):
    """SQLAlchemy model for the automation_action_execution table."""

    __tablename__ = "automation_action_execution"
    __table_args__ = (
        # Unique constraint on execution_key per tenant
        UniqueConstraint(
            "tenant_id",
            "execution_key",
            name="ux_automation_action_execution_tenant_key",
        ),
        # Composite foreign key to automation_actions (tenant_id, id)
        ForeignKeyConstraint(
            ["tenant_id", "action_id"],
            ["dyno_crm.automation_actions.tenant_id", "dyno_crm.automation_actions.id"],
            ondelete="CASCADE",
            name="fk_automation_action_execution_action",
        ),
        # Index on (tenant_id, action_id, status)
        Index(
            "ix_automation_action_execution_tenant_action_status",
            "tenant_id",
            "action_id",
            "status",
        ),
        # Index on (tenant_id, entity_type, entity_id)
        Index(
            "ix_automation_action_execution_entity",
            "tenant_id",
            "entity_type",
            "entity_id",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    pipeline_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    from_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    to_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    list_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    trigger_event: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    execution_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    response_code: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        PGJSONB, nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial repr
        return (
            f"<AutomationActionExecution id={self.id} tenant_id={self.tenant_id} "
            f"action_id={self.action_id} status={self.status}>"
        )


__all__ = ["AutomationActionExecution"]