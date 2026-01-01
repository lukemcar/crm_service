"""SQLAlchemy model for CSAT (Customer Satisfaction) surveys.

The ``csat_survey`` table defines surveys that can be sent to requesters
after tickets are solved. Each survey belongs to a tenant and includes a
name, active flag, and configuration JSON. Audit fields track when
surveys are created and updated and by whom.

Surveys can be created and managed by both tenant-scoped users and
administrators. They are referenced by CSAT responses.
"""

import datetime as _dt
import uuid

from sqlalchemy import (
    Column,
    ForeignKeyConstraint,
    Index,
    String,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.db import Base


class CsatSurvey(Base):
    """Model for the ``csat_survey`` table."""

    __tablename__ = "csat_survey"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_csat_survey_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_csat_survey_tenant_name"),
        Index("ix_csat_survey_tenant", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    # Survey configuration, e.g., rating scales or question templates
    config = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_dt.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_dt.datetime.utcnow, onupdate=_dt.datetime.utcnow
    )
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<CsatSurvey id={self.id} tenant={self.tenant_id} name={self.name}>"


__all__ = ["CsatSurvey"]