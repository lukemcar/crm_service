"""
SQLAlchemy model for Knowledge Base articles.

Articles are the primary documents in the knowledge base.  Each article belongs
to a section and tenant and contains a title, optional slug used for SEO
friendly URLs, and a publish flag.  The article table also tracks audit
fields and enforces tenant scoping and unique slugs per tenant.
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


class KbArticle(Base):
    """Knowledge base article model."""

    __tablename__ = "kb_article"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_kb_article_id_tenant"),
        UniqueConstraint("tenant_id", "lower_slug", name="ux_kb_article_tenant_slug"),
        Index("ix_kb_article_tenant_section", "tenant_id", "kb_section_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    kb_section_id = Column(UUID(as_uuid=True), ForeignKey("kb_section.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    # store lower-case slug in separate column for uniqueness (functional index in DDL)
    slug = Column(String(255))
    lower_slug = Column(String(255))
    is_published = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KbArticle id={self.id} tenant_id={self.tenant_id} title={self.title}>"


__all__ = ["KbArticle"]