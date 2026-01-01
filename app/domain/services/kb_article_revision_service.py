"""
Service layer for Knowledge Base Article Revision entities.

This module implements listing, creation and optional deletion of
knowledge base article revisions.  Revisions are append-only from the
tenant perspective; admin APIs may allow deletion.  The service
computes the next version number when creating a revision if one is not
supplied.  Events are emitted after successful mutations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.kb_article_revision import KbArticleRevision
from app.domain.schemas.kb_article_revision import (
    TenantCreateKbArticleRevision,
    AdminCreateKbArticleRevision,
)
from app.messaging.producers.kb_article_revision_producer import (
    KbArticleRevisionMessageProducer as KbArticleRevisionProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("kb_article_revision_service")


def _snapshot(revision: KbArticleRevision) -> Dict[str, Any]:
    return {
        "id": revision.id,
        "tenant_id": revision.tenant_id,
        "kb_article_id": revision.kb_article_id,
        "version": revision.version,
        "body": revision.body,
        "created_at": revision.created_at.isoformat() if revision.created_at else None,
        "created_by": revision.created_by,
    }


def list_kb_article_revisions(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    kb_article_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[KbArticleRevision], int]:
    """List article revisions with optional tenant and article filters."""
    logger.debug(
        "Listing KB article revisions: tenant_id=%s, article_id=%s, limit=%s, offset=%s",
        tenant_id,
        kb_article_id,
        limit,
        offset,
    )
    query = db.query(KbArticleRevision)
    if tenant_id:
        query = query.filter(KbArticleRevision.tenant_id == tenant_id)
    if kb_article_id:
        query = query.filter(KbArticleRevision.kb_article_id == kb_article_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(KbArticleRevision.version.desc())
    return query.all(), total


def _compute_next_version(db: Session, *, tenant_id: uuid.UUID, kb_article_id: uuid.UUID) -> int:
    """Compute the next revision version number for an article."""
    max_version = (
        db.query(KbArticleRevision.version)
        .filter(
            KbArticleRevision.tenant_id == tenant_id,
            KbArticleRevision.kb_article_id == kb_article_id,
        )
        .order_by(KbArticleRevision.version.desc())
        .first()
    )
    return (max_version[0] + 1) if max_version else 1


def create_kb_article_revision(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateKbArticleRevision | AdminCreateKbArticleRevision,
    created_by: str,
) -> KbArticleRevision:
    """Create an article revision and publish an event."""
    logger.debug(
        "Creating KB article revision: tenant_id=%s, article_id=%s",
        tenant_id,
        request.kb_article_id,
    )
    # Determine version
    version: int
    if isinstance(request, AdminCreateKbArticleRevision) and request.version is not None:
        version = request.version
    else:
        version = _compute_next_version(
            db, tenant_id=tenant_id, kb_article_id=request.kb_article_id
        )
    revision = KbArticleRevision(
        tenant_id=tenant_id,
        kb_article_id=request.kb_article_id,
        version=version,
        body=request.body,
        created_by=created_by,
    )
    db.add(revision)
    commit_or_raise(db, refresh=revision, action="create KB article revision")
    snapshot = _snapshot(revision)
    KbArticleRevisionProducer.send_kb_article_revision_created(
        tenant_id=tenant_id, payload=snapshot
    )
    return revision


def get_kb_article_revision(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    revision_id: uuid.UUID,
) -> KbArticleRevision:
    """Retrieve an article revision by ID within a tenant."""
    revision = (
        db.query(KbArticleRevision)
        .filter(KbArticleRevision.id == revision_id, KbArticleRevision.tenant_id == tenant_id)
        .first()
    )
    if not revision:
        logger.info(
            "KB article revision not found: tenant_id=%s, revision_id=%s",
            tenant_id,
            revision_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article revision not found",
        )
    return revision


def delete_kb_article_revision(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    revision_id: uuid.UUID,
    deleted_by: str,
) -> None:
    """Delete an article revision (admin only) and publish a deleted event."""
    revision = get_kb_article_revision(db, tenant_id=tenant_id, revision_id=revision_id)
    db.delete(revision)
    commit_or_raise(db, action="delete KB article revision")
    KbArticleRevisionProducer.send_kb_article_revision_deleted(
        tenant_id=tenant_id, deleted_dt=datetime.utcnow().isoformat()
    )