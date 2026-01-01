"""
SQLAlchemy model for Knowledge Base sections.

Sections group articles within a category.  Each section belongs to a specific
category and tenant, and has a name, optional description, and active flag.

The table definition mirrors the DDL in 002_support_domain_schema.sql and
includes composite uniqueness and foreign key constraints to enforce tenant
scoping and parent-child relationships.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class KbSection(Base):
    """Knowledge base section model."""

    __tablename__ = "kb_section"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_kb_section_id_tenant"),
        Index("ix_kb_section_tenant_category", "tenant_id", "kb_category_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    kb_category_id = Column(UUID(as_uuid=True), ForeignKey("kb_category.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KbSection id={self.id} tenant_id={self.tenant_id} category_id={self.kb_category_id} name={self.name}>"


__all__ = ["KbSection"]