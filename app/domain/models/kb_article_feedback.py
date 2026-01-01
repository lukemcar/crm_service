"""
SQLAlchemy model for Knowledge Base article feedback.

Feedback allows contacts to indicate whether an article was helpful and leave
comments.  Each feedback entry references a specific article and contact.  It
includes an is_helpful flag and optional comment.  Feedback is append-only
for tenant endpoints; admin endpoints may allow deletion.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class KbArticleFeedback(Base):
    """Knowledge base article feedback model."""

    __tablename__ = "kb_article_feedback"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_kb_article_feedback_id_tenant"),
        Index("ix_kb_article_feedback_tenant_article", "tenant_id", "kb_article_id"),
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["contact.id", "contact.tenant_id"],
            name="fk_kb_article_feedback_contact_tenant",
            ondelete="SET NULL",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    kb_article_id = Column(
        UUID(as_uuid=True), ForeignKey("kb_article.id", ondelete="CASCADE"), nullable=False
    )
    contact_id = Column(UUID(as_uuid=True))

    is_helpful = Column(Boolean, nullable=False)
    comment = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<KbArticleFeedback id={self.id} tenant_id={self.tenant_id} "
            f"article_id={self.kb_article_id} contact_id={self.contact_id}>"
        )


__all__ = ["KbArticleFeedback"]