"""
Pydantic schemas for Knowledge Base Article Feedback domain.

Feedback allows contacts to indicate whether an article was helpful and leave
comments.  These schemas define the request and response models for
creating and retrieving article feedback entries.  Admin endpoints may also
allow deleting feedback.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KbArticleFeedbackBase(BaseModel):
    """Shared attributes for knowledge base article feedback."""

    kb_article_id: uuid.UUID = Field(
        ..., description="Identifier of the article receiving feedback"
    )
    contact_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the contact leaving feedback"
    )
    is_helpful: bool = Field(..., description="Whether the article was helpful")
    comment: Optional[str] = Field(
        default=None, description="Optional feedback comment"
    )


class TenantCreateKbArticleFeedback(KbArticleFeedbackBase):
    """Request model for creating article feedback in tenant context."""

    pass


class AdminCreateKbArticleFeedback(KbArticleFeedbackBase):
    """Request model for creating article feedback via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the feedback"
    )


class KbArticleFeedbackOut(BaseModel):
    """Response model representing a knowledge base article feedback entry."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    kb_article_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    is_helpful: bool
    comment: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "KbArticleFeedbackBase",
    "TenantCreateKbArticleFeedback",
    "AdminCreateKbArticleFeedback",
    "KbArticleFeedbackOut",
]