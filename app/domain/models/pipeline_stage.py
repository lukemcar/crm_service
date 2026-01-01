"""SQLAlchemy model for PipelineStage.

Defines the stages within a pipeline for deals and tickets. Each
PipelineStage is linked to a Pipeline via a foreign key.

Adds tenant_id for data integrity and future partitioning. Enforces that
(pipeline_id, tenant_id) must reference the owning Pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("pipeline_id", "stage_order", name="ux_pipeline_stages_pipeline_order"),
        UniqueConstraint("pipeline_id", "name", name="ux_pipeline_stages_pipeline_name"),
        Index("ix_pipeline_stages_pipeline_id", "pipeline_id"),
        Index("ix_pipeline_stages_tenant", "tenant_id"),
        ForeignKeyConstraint(
            ["pipeline_id", "tenant_id"],
            ["dyno_crm.pipelines.id", "dyno_crm.pipelines.tenant_id"],
            name="fk_pipeline_stages_pipeline_tenant",
            ondelete="CASCADE",
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

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipelines.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stage_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    probability: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
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

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # -----------------------------------------------------------------
    # Parent relationship
    #
    # IMPORTANT:
    # Multiple FK paths exist between pipeline_stages and pipelines due to:
    #   - pipeline_id -> pipelines.id
    #   - (pipeline_id, tenant_id) -> (pipelines.id, pipelines.tenant_id)
    #
    # Explicitly define primaryjoin + foreign_keys to avoid ambiguity and
    # to ensure tenant-safe joins.
    # -----------------------------------------------------------------

    pipeline: Mapped["Pipeline"] = relationship(
        "Pipeline",
        primaryjoin="and_(Pipeline.id==PipelineStage.pipeline_id, Pipeline.tenant_id==PipelineStage.tenant_id)",
        foreign_keys="(PipelineStage.pipeline_id, PipelineStage.tenant_id)",
        back_populates="stages",
    )

    deals: Mapped[List["Deal"]] = relationship(
        "Deal",
        back_populates="stage",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<PipelineStage id={self.id} tenant_id={self.tenant_id} name={self.name} order={self.stage_order}>"
