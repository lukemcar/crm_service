"""SQLAlchemy model for Pipeline.

A pipeline groups stages for deals (and tickets). Each pipeline belongs to
a tenant. Stages are defined in a separate table with a foreign key to
this table.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Pipeline(Base):
    __tablename__ = "pipelines"
    __table_args__ = (
        # Required to support composite tenant-safe foreign keys from child tables.
        UniqueConstraint("id", "tenant_id", name="ux_pipeline_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_pipelines_tenant_name"),
        # Unique constraints for new pipeline identifiers and ordering
        UniqueConstraint("tenant_id", "object_type", "pipeline_key", name="ux_pipeline_tenant_object_key"),
        UniqueConstraint("tenant_id", "object_type", "display_order", name="ux_pipeline_tenant_object_display_order"),
        # Indexes to support multi‑pipeline queries by tenant and object type
        Index("ix_pipelines_tenant", "tenant_id"),
        Index("ix_pipeline_tenant_object_type", "tenant_id", "object_type"),
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

    # New columns introduced in the consolidated CRM change set.  See
    # migrations/liquibase/sql/003_consolidated_crm_change_request.sql for details.
    object_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Type of objects managed by this pipeline (e.g., DEAL, TICKET)",
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Order of this pipeline among pipelines of the same object type"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Flag indicating whether the pipeline is active"
    )
    pipeline_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Stable unique key for API clients to reference this pipeline"
    )
    movement_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="FLEXIBLE",
        comment="Movement enforcement mode for pipeline (FLEXIBLE or RESTRICTED)"
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
        order_by="PipelineStage.display_order",
    )

    # Deals in this pipeline (DB cascades on delete).
    deals: Mapped[List["Deal"]] = relationship(
        "Deal",
        back_populates="pipeline",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Pipeline id={self.id} tenant_id={self.tenant_id} name={self.name}>"
