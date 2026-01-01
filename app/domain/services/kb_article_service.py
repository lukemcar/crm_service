"""
Service layer for Knowledge Base Article entities.

This module implements CRUD operations for knowledge base articles.  Articles
belong to sections and tenants.  The service enforces tenant scoping,
handles transactions via ``commit_or_raise`` and emits events through the
message producer after successful mutations.  Slugs are normalized to
lower-case for uniqueness across a tenant.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.kb_article import KbArticle
from app.domain.schemas.kb_article import (
    TenantCreateKbArticle,
    AdminCreateKbArticle,
    KbArticleUpdate,
)
from app.domain.schemas.events.kb_article_event import KbArticleDelta
from app.messaging.producers.kb_article_producer import (
    KbArticleMessageProducer as KbArticleProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("kb_article_service")


def _snapshot(article: KbArticle) -> Dict[str, Any]:
    return {
        "id": article.id,
        "tenant_id": article.tenant_id,
        "kb_section_id": article.kb_section_id,
        "title": article.title,
        "slug": article.slug,
        "is_published": article.is_published,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        "created_by": article.created_by,
        "updated_by": article.updated_by,
    }


def _compute_delta(article: KbArticle, updates: Dict[str, Any]) -> KbArticleDelta:
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(article, field)
        if current != value:
            changed[field] = value
    return KbArticleDelta(base_fields=changed or None)


def list_kb_articles(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    kb_section_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[KbArticle], int]:
    """List articles with optional tenant and section filters."""
    logger.debug(
        "Listing KB articles: tenant_id=%s, section_id=%s, limit=%s, offset=%s",
        tenant_id,
        kb_section_id,
        limit,
        offset,
    )
    query = db.query(KbArticle)
    if tenant_id:
        query = query.filter(KbArticle.tenant_id == tenant_id)
    if kb_section_id:
        query = query.filter(KbArticle.kb_section_id == kb_section_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(KbArticle.created_at.desc())
    return query.all(), total


def _normalize_slug(slug: Optional[str]) -> tuple[str | None, str | None]:
    """Return a tuple of (slug, lower_slug) normalized for storage."""
    if not slug:
        return None, None
    lower_slug = slug.lower()
    return slug, lower_slug


def create_kb_article(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateKbArticle | AdminCreateKbArticle,
    created_by: str,
) -> KbArticle:
    """Create an article and publish a created event."""
    logger.debug(
        "Creating KB article: tenant_id=%s, section_id=%s, title=%s",
        tenant_id,
        request.kb_section_id,
        request.title,
    )
    slug, lower_slug = _normalize_slug(request.slug)
    article = KbArticle(
        tenant_id=tenant_id,
        kb_section_id=request.kb_section_id,
        title=request.title,
        slug=slug,
        lower_slug=lower_slug,
        is_published=request.is_published if request.is_published is not None else False,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(article)
    commit_or_raise(db, refresh=article, action="create KB article")
    snapshot = _snapshot(article)
    KbArticleProducer.send_kb_article_created(tenant_id=tenant_id, payload=snapshot)
    return article


def get_kb_article(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    article_id: uuid.UUID,
) -> KbArticle:
    """Retrieve an article by ID within a tenant."""
    article = (
        db.query(KbArticle)
        .filter(KbArticle.id == article_id, KbArticle.tenant_id == tenant_id)
        .first()
    )
    if not article:
        logger.info(
            "KB article not found: tenant_id=%s, article_id=%s", tenant_id, article_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


def update_kb_article(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    article_id: uuid.UUID,
    request: KbArticleUpdate,
    updated_by: str,
) -> KbArticle:
    """Update an article and publish an updated event if changed."""
    article = get_kb_article(db, tenant_id=tenant_id, article_id=article_id)
    updates: Dict[str, Any] = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.slug is not None:
        slug, lower_slug = _normalize_slug(request.slug)
        updates["slug"] = slug
        updates["lower_slug"] = lower_slug
    if request.is_published is not None:
        updates["is_published"] = request.is_published

    delta = _compute_delta(article, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(article, field, value)
        article.updated_by = updated_by
        article.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=article, action="update KB article")
        snapshot = _snapshot(article)
        KbArticleProducer.send_kb_article_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return article


def delete_kb_article(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    article_id: uuid.UUID,
    deleted_by: str,
) -> None:
    """Delete an article and publish a deleted event."""
    article = get_kb_article(db, tenant_id=tenant_id, article_id=article_id)
    db.delete(article)
    commit_or_raise(db, action="delete KB article")
    KbArticleProducer.send_kb_article_deleted(
        tenant_id=tenant_id, deleted_dt=datetime.utcnow().isoformat()
    )