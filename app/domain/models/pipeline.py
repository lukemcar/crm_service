"""SQLAlchemy model for Pipeline.

A pipeline groups stages for deals (and tickets). Each pipeline belongs to
a tenant. Stages are defined in a separate table with a foreign key to
this table.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Pipeline(Base):
    __tablename__ = "pipelines"
    __table_args__ = (
        # Required to support composite tenant-safe foreign keys from child tables.
        UniqueConstraint("id", "tenant_id", name="ux_pipeline_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_pipelines_tenant_name"),
        Index("ix_pipelines_tenant", "tenant_id"),
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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    # -----------------------------------------------------------------
    # Child collections
    #
    # IMPORTANT:
    # The schema uses BOTH:
    #   - FK(pipeline_id) -> pipelines(id)
    #   - FK(pipeline_id, tenant_id) -> pipelines(id, tenant_id)
    #
    # That produces multiple FK paths between the same tables, which causes
    # SQLAlchemy AmbiguousForeignKeysError unless we explicitly tell it which
    # columns to use for the relationship. We use the composite join for
    # tenant-safe relationship navigation.
    # -----------------------------------------------------------------

    stages: Mapped[List["PipelineStage"]] = relationship(
        "PipelineStage",
        primaryjoin="and_(Pipeline.id==PipelineStage.pipeline_id, Pipeline.tenant_id==PipelineStage.tenant_id)",
        foreign_keys="(PipelineStage.pipeline_id, PipelineStage.tenant_id)",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PipelineStage.stage_order",
    )

    # Deals in this pipeline (DB cascades on delete).
    deals: Mapped[List["Deal"]] = relationship(
        "Deal",
        back_populates="pipeline",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Pipeline id={self.id} tenant_id={self.tenant_id} name={self.name}>"
