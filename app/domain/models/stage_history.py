"""
SQLAlchemy model for StageHistory.

This table records stage transitions for CRM entities (e.g. deals or leads).
Each row captures the entity context (type and ID), the previous and
new pipeline stages, and audit metadata including when and by whom
the transition occurred. Stage history entries are append-only; they
are never updated or deleted.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Index,
    ForeignKeyConstraint,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StageHistory(Base):
    """SQLAlchemy model for the ``stage_history`` table."""

    __tablename__ = "stage_history"
    __table_args__ = (
        # Composite foreign key to pipelines (tenant_id, pipeline_id)
        ForeignKeyConstraint(
            ["tenant_id", "pipeline_id"],
            ["dyno_crm.pipelines.tenant_id", "dyno_crm.pipelines.id"],
            ondelete="SET NULL",
            name="fk_stage_history_pipeline",
        ),
        # Foreign keys to pipeline stages (set null on delete)
        ForeignKeyConstraint(
            ["from_stage_id", "tenant_id"],
            ["dyno_crm.pipeline_stages.id", "dyno_crm.pipeline_stages.tenant_id"],
            ondelete="SET NULL",
            name="fk_stage_history_from_stage",
        ),
        ForeignKeyConstraint(
            ["to_stage_id", "tenant_id"],
            ["dyno_crm.pipeline_stages.id", "dyno_crm.pipeline_stages.tenant_id"],
            ondelete="SET NULL",
            name="fk_stage_history_to_stage",
        ),
        # Foreign key to tenant_user_shadow for changed_by_user_id (composite)
        ForeignKeyConstraint(
            ["tenant_id", "changed_by_user_id"],
            ["tenant_user_shadow.tenant_id", "tenant_user_shadow.user_id"],
            ondelete="SET NULL",
            name="fk_stage_history_changed_by_user",
        ),
        # Index for quick lookup by entity context
        Index(
            "ix_stage_history_entity",
            "tenant_id",
            "entity_type",
            "entity_id",
        ),
        # Index for filtering by pipeline
        Index("ix_stage_history_pipeline", "tenant_id", "pipeline_id"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
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
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial repr
        return (
            f"<StageHistory id={self.id} tenant_id={self.tenant_id} "
            f"entity={self.entity_type}:{self.entity_id} from={self.from_stage_id} "
            f"to={self.to_stage_id}>"
        )


__all__ = ["StageHistory"]