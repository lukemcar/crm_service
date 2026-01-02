"""
Admin‑scoped endpoints for knowledge base article revisions.

This router exposes endpoints to list, create, retrieve and delete article
revisions across tenants.  Administrators specify the tenant via query
parameters when retrieving or modifying revisions.  Audit fields are
populated from the ``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_article_revision import (
    AdminCreateKbArticleRevision,
    KbArticleRevisionOut,
)
from app.domain.services import kb_article_revision_service


router = APIRouter(
    prefix="/admin/kb_article_revisions",
    tags=["Knowledge Base Article Revisions"],
)


@router.get("", response_model=List[KbArticleRevisionOut])
def list_kb_article_revisions_admin_endpoint(
    tenant_id: Optional[UUID] = Query(
        None, description="If provided, filters revisions by tenant"
    ),
    kb_article_id: Optional[UUID] = Query(
        None, description="If provided, filters revisions by article"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbArticleRevisionOut]:
    """List knowledge base article revisions across tenants with optional filters."""
    revisions, _ = kb_article_revision_service.list_kb_article_revisions(
        db,
        tenant_id=tenant_id,
        kb_article_id=kb_article_id,
        limit=limit,
        offset=offset,
    )
    return [KbArticleRevisionOut.model_validate(r, from_attributes=True) for r in revisions]


@router.post("", response_model=KbArticleRevisionOut, status_code=status.HTTP_201_CREATED)
def create_kb_article_revision_admin_endpoint(
    revision_in: AdminCreateKbArticleRevision,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbArticleRevisionOut:
    """Create an article revision via the admin API specifying the tenant."""
    created_user = x_user or "anonymous"
    revision = kb_article_revision_service.create_kb_article_revision(
        db,
        tenant_id=revision_in.tenant_id,
        request=revision_in,
        created_by=created_user,
    )
    return KbArticleRevisionOut.model_validate(revision, from_attributes=True)


@router.get("/{revision_id}", response_model=KbArticleRevisionOut)
def get_kb_article_revision_admin_endpoint(
    revision_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the revision to scope the search"
    ),
    db: Session = Depends(get_db),
) -> KbArticleRevisionOut:
    """Retrieve an article revision via the admin API."""
    revision = kb_article_revision_service.get_kb_article_revision(
        db,
        tenant_id=tenant_id,
        revision_id=revision_id,
    )
    return KbArticleRevisionOut.model_validate(revision, from_attributes=True)


@router.delete("/{revision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kb_article_revision_admin_endpoint(
    revision_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the revision to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an article revision via the admin API."""
    kb_article_revision_service.delete_kb_article_revision(
        db,
        tenant_id=tenant_id,
        revision_id=revision_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_article_revisions_admin_endpoint",
    "create_kb_article_revision_admin_endpoint",
    "get_kb_article_revision_admin_endpoint",
    "delete_kb_article_revision_admin_endpoint",
]