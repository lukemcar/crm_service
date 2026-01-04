"""
SQLAlchemy model for automation actions in the CRM.

Automation actions represent workflow rules that respond to record events
and execute predefined actions (e.g. send notifications, update fields).
Each action belongs to a tenant and targets exactly one scope: a specific
record, an entire pipeline, a pipeline stage, or a list.  The action
defines a trigger event, optional conditions expressed as JSON, an
action type and additional configuration.  Actions are enabled by
default, ordered by priority, and may inherit pipeline‑level actions
when scoped to stages or lists.

The underlying table is created via Liquibase and resides in the
``dyno_crm`` schema.  Check constraints enforce that exactly one
scope target is provided.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    JSON,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AutomationAction(Base):
    """SQLAlchemy model mapping to ``dyno_crm.automation_action``.

    Automation actions orchestrate workflows triggered by CRM events.  They
    are scoped to exactly one target (record, pipeline, stage or list)
    and include a trigger event name, optional condition expression,
    action type and configuration.  Actions are tenant‑scoped and may
    be enabled/disabled or inherited by nested scopes.
    """

    __tablename__ = "automation_action"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_automation_action_id_tenant"),
        Index(
            "ix_automation_action_tenant_entity_enabled",
            "tenant_id",
            "entity_type",
            "enabled",
        ),
        Index(
            "ix_automation_action_tenant_scope",
            "tenant_id",
            "scope_type",
        ),
        Index(
            "ix_automation_action_tenant_record",
            "tenant_id",
            "record_type",
            "record_id",
        ),
        Index(
            "ix_automation_action_tenant_pipeline",
            "tenant_id",
            "pipeline_id",
        ),
        Index(
            "ix_automation_action_tenant_pipeline_stage",
            "tenant_id",
            "pipeline_stage_id",
        ),
        Index(
            "ix_automation_action_tenant_list",
            "tenant_id",
            "list_id",
        ),
        # Enforce that exactly one scope target is provided
        CheckConstraint(
            "(record_id IS NOT NULL)::int + "
            "(pipeline_id IS NOT NULL)::int + "
            "(pipeline_stage_id IS NOT NULL)::int + "
            "(list_id IS NOT NULL)::int = 1",
            name="ck_automation_action_scope_target",
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
    # Type of entity that triggers this action (e.g. CONTACT, DEAL)
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # Scope type defines which field identifies the scope
    scope_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # Record scope: type of record targeted (must match entity_type for record scope)
    record_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    # Pipeline scope
    pipeline_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    # Stage scope
    pipeline_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    # List scope
    list_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    # Event that triggers this action (e.g. created, updated)
    trigger_event: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    # Optional conditions encoded as JSON (expression to evaluate)
    condition_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    # Type of action to perform (e.g. send_email, update_field)
    action_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # Action configuration encoded as JSON
    config_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    inherit_pipeline_actions: Mapped[bool] = mapped_column(
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

    def __repr__(self) -> str:
        return (
            f"<AutomationAction id={self.id} tenant={self.tenant_id} entity={self.entity_type} "
            f"scope={self.scope_type}>"
        )


__all__ = ["AutomationAction"]