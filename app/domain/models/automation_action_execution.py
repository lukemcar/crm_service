"""
SQLAlchemy model for automation action execution records.

Automation action executions record each run of an automation action on a
specific entity.  Executions are tied to a tenant and reference the
automation action that triggered them.  A unique execution_key is used
to ensure idempotent processing.  Status tracks the lifecycle of an
execution (PENDING, IN_PROGRESS, SUCCEEDED, FAILED), along with
context information such as response codes and error messages.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Integer,
    String,
    JSON,
    DateTime,
    UniqueConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AutomationActionExecution(Base):
    """SQLAlchemy model mapping to ``dyno_crm.automation_action_execution``.

    Each record captures the execution of an automation action for a
    particular entity at a point in time.  Executions are uniquely
    identified by a (tenant_id, execution_key) pair to support
    idempotency.  The status field indicates the current execution
    state, and optional timestamps track when execution started and
    completed.
    """

    __tablename__ = "automation_action_execution"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "execution_key",
            name="ux_automation_action_execution_tenant_key",
        ),
        Index(
            "ix_automation_action_execution_tenant_action_status",
            "tenant_id",
            "action_id",
            "status",
        ),
        Index(
            "ix_automation_action_execution_tenant_entity",
            "tenant_id",
            "entity_type",
            "entity_id",
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
    action_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.automation_action.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    pipeline_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    from_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    to_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    list_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    trigger_event: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    execution_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    response_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return (
            f"<AutomationActionExecution id={self.id} tenant={self.tenant_id} "
            f"action={self.action_id} status={self.status}>"
        )


__all__ = ["AutomationActionExecution"]