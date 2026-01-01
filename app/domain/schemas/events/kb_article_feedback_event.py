"""
Event models for Knowledge Base Article Feedback lifecycle.

Defines payload schemas for knowledge base article feedback events emitted via
the messaging layer.  Feedback entries are append-only; events exist for
creation and deletion.  Update events are not supported because feedback
cannot be modified via tenant routes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KbArticleFeedbackCreatedEvent(BaseModel):
    """Payload for a kb_article_feedback.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full knowledge base article feedback snapshot after creation"
    )


class KbArticleFeedbackDeletedEvent(BaseModel):
    """Payload for a kb_article_feedback.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the article feedback was deleted",
    )


__all__ = [
    "KbArticleFeedbackCreatedEvent",
    "KbArticleFeedbackDeletedEvent",
]