"""
Pydantic schemas for Knowledge Base Article Revision domain.

Revisions capture historical versions of articles.  Tenants can create new
revisions by providing the article ID and body; the version number is
computed automatically.  Revisions are append-only and are read-only via
tenant routes after creation.  Admin routes may allow deletion if needed.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KbArticleRevisionBase(BaseModel):
    """Shared attributes for knowledge base article revisions."""

    kb_article_id: uuid.UUID = Field(
        ..., description="Identifier of the article being revised"
    )
    body: str = Field(..., description="Full body of the article revision")


class TenantCreateKbArticleRevision(KbArticleRevisionBase):
    """Request model for creating an article revision in tenant context."""

    # version is not provided; it will be computed by the service
    pass


class AdminCreateKbArticleRevision(KbArticleRevisionBase):
    """Request model for creating an article revision via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the article revision"
    )
    version: Optional[int] = Field(
        default=None, description="Optional explicit version number for the revision"
    )


class KbArticleRevisionOut(BaseModel):
    """Response model representing an article revision."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    kb_article_id: uuid.UUID
    version: int
    body: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "KbArticleRevisionBase",
    "TenantCreateKbArticleRevision",
    "AdminCreateKbArticleRevision",
    "KbArticleRevisionOut",
]