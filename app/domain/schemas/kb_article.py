"""
Pydantic schemas for Knowledge Base Article domain.

Articles are the primary knowledge base content.  These schemas define the
request and response models for articles.  The create schemas require the
parent section ID and article title; slug is optional and will be
normalized to lower-case during service processing.  Update schemas allow
modifying title, slug, publication status, and optional fields.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KbArticleBase(BaseModel):
    """Shared attributes for knowledge base articles."""

    kb_section_id: uuid.UUID = Field(
        ..., description="Identifier of the parent section for this article"
    )
    title: str = Field(..., max_length=255, description="Article title")
    slug: Optional[str] = Field(
        default=None, max_length=255, description="Optional URL slug for the article"
    )
    is_published: Optional[bool] = Field(
        default=False, description="Whether the article is published"
    )


class TenantCreateKbArticle(KbArticleBase):
    """Request model for creating an article in tenant context."""

    pass


class AdminCreateKbArticle(KbArticleBase):
    """Request model for creating an article via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the article")


class KbArticleUpdate(BaseModel):
    """Request model for updating an existing article."""

    title: Optional[str] = Field(default=None, max_length=255, description="Article title")
    slug: Optional[str] = Field(
        default=None, max_length=255, description="Optional URL slug for the article"
    )
    is_published: Optional[bool] = Field(
        default=None, description="Whether the article is published"
    )


class KbArticleOut(BaseModel):
    """Response model representing a knowledge base article."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    kb_section_id: uuid.UUID
    title: str
    slug: Optional[str] = None
    is_published: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "KbArticleBase",
    "TenantCreateKbArticle",
    "AdminCreateKbArticle",
    "KbArticleUpdate",
    "KbArticleOut",
]