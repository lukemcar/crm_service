"""
Admin‑scoped endpoints for knowledge base articles.

This router exposes CRUD operations on KB articles across tenants.
Administrators can list articles (optionally filtering by tenant or section),
create articles specifying the tenant, update articles, and delete articles.
Audit fields are populated from the ``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Path, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_article import (
    AdminCreateKbArticle,
    KbArticleUpdate,
    KbArticleOut,
)
from app.domain.services import kb_article_service


router = APIRouter(
    prefix="/admin/kb_articles",
    tags=["Knowledge Base Articles"],
)


@router.get("", response_model=List[KbArticleOut])
def list_kb_articles_admin_endpoint(
    tenant_id: Optional[UUID] = Query(
        None, description="If provided, filters articles by tenant"
    ),
    kb_section_id: Optional[UUID] = Query(
        None, description="If provided, filters articles by section"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbArticleOut]:
    """List knowledge base articles across tenants with optional filters."""
    articles, _ = kb_article_service.list_kb_articles(
        db,
        tenant_id=tenant_id,
        kb_section_id=kb_section_id,
        limit=limit,
        offset=offset,
    )
    return [KbArticleOut.model_validate(a, from_attributes=True) for a in articles]


@router.post("", response_model=KbArticleOut, status_code=status.HTTP_201_CREATED)
def create_kb_article_admin_endpoint(
    article_in: AdminCreateKbArticle,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbArticleOut:
    """Create a knowledge base article via the admin API specifying the tenant."""
    created_user = x_user or "anonymous"
    article = kb_article_service.create_kb_article(
        db,
        tenant_id=article_in.tenant_id,
        request=article_in,
        created_by=created_user,
    )
    return KbArticleOut.model_validate(article, from_attributes=True)


@router.get("/{article_id}", response_model=KbArticleOut)
def get_kb_article_admin_endpoint(
    article_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the article to scope the search"
    ),
    db: Session = Depends(get_db),
) -> KbArticleOut:
    """Retrieve a knowledge base article via the admin API."""
    article = kb_article_service.get_kb_article(
        db,
        tenant_id=tenant_id,
        article_id=article_id,
    )
    return KbArticleOut.model_validate(article, from_attributes=True)


@router.put("/{article_id}", response_model=KbArticleOut)
def update_kb_article_admin_endpoint(
    article_id: UUID,
    article_update: KbArticleUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the article to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbArticleOut:
    """Update a knowledge base article via the admin API."""
    updated_user = x_user or "anonymous"
    article = kb_article_service.update_kb_article(
        db,
        tenant_id=tenant_id,
        article_id=article_id,
        request=article_update,
        updated_by=updated_user,
    )
    return KbArticleOut.model_validate(article, from_attributes=True)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kb_article_admin_endpoint(
    article_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the article to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a knowledge base article via the admin API."""
    kb_article_service.delete_kb_article(
        db,
        tenant_id=tenant_id,
        article_id=article_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_articles_admin_endpoint",
    "create_kb_article_admin_endpoint",
    "get_kb_article_admin_endpoint",
    "update_kb_article_admin_endpoint",
    "delete_kb_article_admin_endpoint",
]