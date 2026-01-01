"""
Event models for Knowledge Base Article Revision lifecycle.

Defines payload schemas for knowledge base article revision events emitted via
the messaging layer.  Revisions are append-only; events exist for creation
and deletion.  Update events are not supported because revisions cannot be
modified via tenant routes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KbArticleRevisionCreatedEvent(BaseModel):
    """Payload for a kb_article_revision.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base article revision snapshot after creation"
    )


class KbArticleRevisionDeletedEvent(BaseModel):
    """Payload for a kb_article_revision.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the article revision was deleted",
    )


__all__ = [
    "KbArticleRevisionCreatedEvent",
    "KbArticleRevisionDeletedEvent",
]