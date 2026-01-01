"""
Tenant‑scoped endpoints for knowledge base article revisions.

This router exposes endpoints to list, create, and retrieve article
revisions within a tenant.  Revisions are append‑only and cannot be
modified via tenant APIs.  The article ID is specified in the path.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_article_revision import (
    TenantCreateKbArticleRevision,
    KbArticleRevisionOut,
)
from app.domain.services import kb_article_revision_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/kb_articles/{article_id}/revisions",
    tags=["Knowledge Base Article Revisions"],
)


@router.get("", response_model=List[KbArticleRevisionOut])
def list_kb_article_revisions_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
) -> List[KbArticleRevisionOut]:
    """List revisions for a specific article within a tenant."""
    revisions, _ = kb_article_revision_service.list_kb_article_revisions(
        db,
        tenant_id=tenant_id,
        kb_article_id=article_id,
    )
    return [KbArticleRevisionOut.model_validate(r, from_attributes=True) for r in revisions]


@router.post("", response_model=KbArticleRevisionOut, status_code=status.HTTP_201_CREATED)
def create_kb_article_revision_tenant_endpoint(
    revision_in: TenantCreateKbArticleRevision,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbArticleRevisionOut:
    """Create a revision for an article within a tenant."""
    created_user = x_user or "anonymous"
    # Ensure path article_id matches body
    if revision_in.kb_article_id != article_id:
        raise ValueError("Path article_id does not match body kb_article_id")
    revision = kb_article_revision_service.create_kb_article_revision(
        db,
        tenant_id=tenant_id,
        request=revision_in,
        created_by=created_user,
    )
    return KbArticleRevisionOut.model_validate(revision, from_attributes=True)


@router.get("/{revision_id}", response_model=KbArticleRevisionOut)
def get_kb_article_revision_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    revision_id: UUID = Path(..., description="Revision ID"),
    db: Session = Depends(get_db),
) -> KbArticleRevisionOut:
    """Retrieve a specific article revision within a tenant."""
    revision = kb_article_revision_service.get_kb_article_revision(
        db,
        tenant_id=tenant_id,
        revision_id=revision_id,
    )
    # Optionally verify article_id matches but not necessary; revision belongs to article
    return KbArticleRevisionOut.model_validate(revision, from_attributes=True)


__all__ = [
    "list_kb_article_revisions_tenant_endpoint",
    "create_kb_article_revision_tenant_endpoint",
    "get_kb_article_revision_tenant_endpoint",
]