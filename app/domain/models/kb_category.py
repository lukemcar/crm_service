"""
SQLAlchemy model for Knowledge Base categories.

Each tenant can organize their knowledge base content into categories.  A category
has a name, optional description, and an active flag.  Categories are the
top-level grouping for knowledge base articles and sections.

The table definition matches the DDL in 002_support_domain_schema.sql.  It
enforces tenant scoping via composite uniqueness constraints and provides
timestamp and user audit fields.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.core.db import Base


class KbCategory(Base):
    """Knowledge base category model."""

    __tablename__ = "kb_category"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_kb_category_id_tenant"),
        UniqueConstraint("tenant_id", "name", name="ux_kb_category_tenant_name"),
        Index("ix_kb_category_tenant", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KbCategory id={self.id} tenant_id={self.tenant_id} name={self.name}>"


__all__ = ["KbCategory"]