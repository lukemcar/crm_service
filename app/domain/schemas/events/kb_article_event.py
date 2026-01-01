"""
Event models for Knowledge Base Article lifecycle.

Defines payload schemas for knowledge base article events emitted via the
messaging layer.  Each event corresponds to a CRUD operation on KbArticle
entities.  A delta structure describes modifications for update events.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KbArticleDelta(BaseModel):
    """Represents the set of changed base fields for a knowledge base article."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class KbArticleCreatedEvent(BaseModel):
    """Payload for a kb_article.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base article snapshot after creation"
    )


class KbArticleUpdatedEvent(BaseModel):
    """Payload for a kb_article.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: KbArticleDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base article snapshot after update"
    )


class KbArticleDeletedEvent(BaseModel):
    """Payload for a kb_article.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the article was deleted",
    )


__all__ = [
    "KbArticleDelta",
    "KbArticleCreatedEvent",
    "KbArticleUpdatedEvent",
    "KbArticleDeletedEvent",
]