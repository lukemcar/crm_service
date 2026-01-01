"""
Tenant‑scoped endpoints for knowledge base articles.

This router exposes CRUD operations on knowledge base articles within a
tenant.  Tenants can list, create, update and delete articles.  Articles
belong to sections and tenants.  Audit fields are populated from the
``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_article import (
    TenantCreateKbArticle,
    KbArticleUpdate,
    KbArticleOut,
)
from app.domain.services import kb_article_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/kb_articles",
    tags=["Knowledge Base Articles"],
)


@router.get("", response_model=List[KbArticleOut])
def list_kb_articles_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    kb_section_id: Optional[UUID] = Query(
        None, description="If provided, filters articles by section"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbArticleOut]:
    """List knowledge base articles for a tenant, optionally filtered by section."""
    articles, _ = kb_article_service.list_kb_articles(
        db,
        tenant_id=tenant_id,
        kb_section_id=kb_section_id,
        limit=limit,
        offset=offset,
    )
    return [KbArticleOut.model_validate(a, from_attributes=True) for a in articles]


@router.post("", response_model=KbArticleOut, status_code=status.HTTP_201_CREATED)
def create_kb_article_tenant_endpoint(
    article_in: TenantCreateKbArticle,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbArticleOut:
    """Create a knowledge base article within a tenant."""
    created_user = x_user or "anonymous"
    article = kb_article_service.create_kb_article(
        db,
        tenant_id=tenant_id,
        request=article_in,
        created_by=created_user,
    )
    return KbArticleOut.model_validate(article, from_attributes=True)


@router.get("/{article_id}", response_model=KbArticleOut)
def get_kb_article_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
) -> KbArticleOut:
    """Retrieve a knowledge base article within a tenant."""
    article = kb_article_service.get_kb_article(
        db,
        tenant_id=tenant_id,
        article_id=article_id,
    )
    return KbArticleOut.model_validate(article, from_attributes=True)


@router.put("/{article_id}", response_model=KbArticleOut)
def update_kb_article_tenant_endpoint(
    article_update: KbArticleUpdate,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbArticleOut:
    """Update a knowledge base article within a tenant."""
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
def delete_kb_article_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a knowledge base article within a tenant."""
    kb_article_service.delete_kb_article(
        db,
        tenant_id=tenant_id,
        article_id=article_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_articles_tenant_endpoint",
    "create_kb_article_tenant_endpoint",
    "get_kb_article_tenant_endpoint",
    "update_kb_article_tenant_endpoint",
    "delete_kb_article_tenant_endpoint",
]