"""
SQLAlchemy model for stage history.

The stage history table records transitions of entities between pipeline
stages.  It captures the pipeline, the previous stage, the new stage,
and metadata about when and who initiated the change.  This model
enables auditing of stage movements for stage‑based CRM entities.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    DateTime,
    UniqueConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StageHistory(Base):
    """SQLAlchemy model mapping to ``dyno_crm.stage_history``.

    Each record stores a change of stage for a particular entity within
    a pipeline.  It contains references to the pipeline and both
    stages (from and to), along with the entity type and ID.
    """

    __tablename__ = "stage_history"
    __table_args__ = (
        Index(
            "ix_stage_history_tenant_entity",
            "tenant_id",
            "entity_type",
            "entity_id",
        ),
        Index(
            "ix_stage_history_tenant_pipeline",
            "tenant_id",
            "pipeline_id",
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
        ForeignKey("dyno_crm.pipeline.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipeline_stage.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipeline_stage.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.tenant_user_shadow.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<StageHistory id={self.id} tenant={self.tenant_id} entity={self.entity_type}"
            f" from={self.from_stage_id} to={self.to_stage_id}>"
        )


__all__ = ["StageHistory"]