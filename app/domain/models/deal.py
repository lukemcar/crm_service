"""SQLAlchemy model for Deal.

Represents a sales opportunity. Each deal belongs to a tenant, a pipeline
and a pipeline stage.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("ix_deals_tenant", "tenant_id"),
        Index("ix_deals_pipeline", "pipeline_id"),
        Index("ix_deals_stage", "stage_id"),
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

    amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    expected_close_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # IMPORTANT: schema-qualified FKs because tables live in dyno_crm schema
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipelines.id", ondelete="CASCADE"),
        nullable=False,
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.pipeline_stages.id", ondelete="CASCADE"),
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

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship(
        "Pipeline",
        back_populates="deals",
    )

    stage: Mapped["PipelineStage"] = relationship(
        "PipelineStage",
        back_populates="deals",
    )

    def __repr__(self) -> str:
        return f"<Deal id={self.id} name={self.name} amount={self.amount}>"
