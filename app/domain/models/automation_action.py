"""
SQLAlchemy model for AutomationAction.

This model represents an automation action configured by a tenant.  An
automation action can target a specific record, pipeline, pipeline stage
or list, depending on its scope.  It defines a trigger event, optional
conditions, an action type and configuration payload, and execution
parameters such as priority and enabled state.

Note: This is an initial skeleton implementation.  Foreign key
constraints and check constraints described in the implementation
guide are not yet fully enforced.  See future iterations for
completion.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AutomationAction(Base):
    __tablename__ = "automation_actions"
    __table_args__ = (
        # Unique constraint on (tenant_id, id) to ensure tenant isolation
        UniqueConstraint("tenant_id", "id", name="ux_automation_actions_tenant_id"),
        # Check constraint ensures exactly one target column is populated.  Each
        # boolean cast counts True as 1 and False/NULL as 0, summing to 1 when
        # exactly one is non-null.  See guide for scope check constraint【480489992503603†L220-L224】.
        CheckConstraint(
            "((record_id IS NOT NULL)::int + (pipeline_id IS NOT NULL)::int + "
            "(pipeline_stage_id IS NOT NULL)::int + (list_id IS NOT NULL)::int) = 1",
            name="chk_automation_actions_single_scope",
        ),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Target columns: exactly one should be set.  All are nullable here.
    record_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    record_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    pipeline_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipelines.id", ondelete="SET NULL"),
        nullable=True,
    )
    pipeline_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipeline_stages.id", ondelete="SET NULL"),
        nullable=True,
    )
    list_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.lists.id", ondelete="SET NULL"),
        nullable=True,
    )
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)
    condition_json: Mapped[Optional[dict]] = mapped_column(PGJSONB, nullable=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    config_json: Mapped[Optional[dict]] = mapped_column(PGJSONB, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    inherit_pipeline_actions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AutomationAction id={self.id} tenant={self.tenant_id} entity={self.entity_type} "
            f"scope={self.scope_type}>"
        )