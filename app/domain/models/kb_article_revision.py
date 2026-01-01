"""
SQLAlchemy model for Knowledge Base article revisions.

Each article can have multiple revisions, identified by a version number and
containing the full body of the article at that point in time.  Revisions
are append-only; once created they cannot be updated or deleted via tenant
endpoints (admin may choose to delete if needed).  The table includes
foreign key constraints to the parent article and tenant.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class KbArticleRevision(Base):
    """Knowledge base article revision model."""

    __tablename__ = "kb_article_revision"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_kb_article_revision_id_tenant"),
        UniqueConstraint(
            "tenant_id", "kb_article_id", "version", name="ux_kb_article_revision_unique"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    kb_article_id = Column(
        UUID(as_uuid=True), ForeignKey("kb_article.id", ondelete="CASCADE"), nullable=False
    )

    version = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<KbArticleRevision id={self.id} tenant_id={self.tenant_id} "
            f"article_id={self.kb_article_id} version={self.version}>"
        )


__all__ = ["KbArticleRevision"]