"""
Service layer for Knowledge Base Article Feedback entities.

This module implements listing, creation and optional deletion of
knowledge base article feedback entries.  Feedback entries allow
contacts to rate an article and leave comments.  The service enforces
tenant scoping and emits events after successful mutations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.kb_article_feedback import KbArticleFeedback
from app.domain.schemas.kb_article_feedback import (
    TenantCreateKbArticleFeedback,
    AdminCreateKbArticleFeedback,
)
from app.messaging.producers.kb_article_feedback_producer import (
    KbArticleFeedbackMessageProducer as KbArticleFeedbackProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("kb_article_feedback_service")


def _snapshot(feedback: KbArticleFeedback) -> Dict[str, Any]:
    return {
        "id": feedback.id,
        "tenant_id": feedback.tenant_id,
        "kb_article_id": feedback.kb_article_id,
        "contact_id": feedback.contact_id,
        "is_helpful": feedback.is_helpful,
        "comment": feedback.comment,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        "created_by": feedback.created_by,
    }


def list_kb_article_feedback(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    kb_article_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[KbArticleFeedback], int]:
    """List article feedback with optional tenant and article filters."""
    logger.debug(
        "Listing KB article feedback: tenant_id=%s, article_id=%s, limit=%s, offset=%s",
        tenant_id,
        kb_article_id,
        limit,
        offset,
    )
    query = db.query(KbArticleFeedback)
    if tenant_id:
        query = query.filter(KbArticleFeedback.tenant_id == tenant_id)
    if kb_article_id:
        query = query.filter(KbArticleFeedback.kb_article_id == kb_article_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(KbArticleFeedback.created_at.desc())
    return query.all(), total


def create_kb_article_feedback(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateKbArticleFeedback | AdminCreateKbArticleFeedback,
    created_by: str,
) -> KbArticleFeedback:
    """Create article feedback and publish an event."""
    logger.debug(
        "Creating KB article feedback: tenant_id=%s, article_id=%s",
        tenant_id,
        request.kb_article_id,
    )
    feedback = KbArticleFeedback(
        tenant_id=tenant_id,
        kb_article_id=request.kb_article_id,
        contact_id=request.contact_id,
        is_helpful=request.is_helpful,
        comment=request.comment,
        created_by=created_by,
    )
    db.add(feedback)
    commit_or_raise(db, refresh=feedback, action="create KB article feedback")
    snapshot = _snapshot(feedback)
    KbArticleFeedbackProducer.send_kb_article_feedback_created(
        tenant_id=tenant_id, payload=snapshot
    )
    return feedback


def get_kb_article_feedback(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    feedback_id: uuid.UUID,
) -> KbArticleFeedback:
    """Retrieve feedback by ID within a tenant."""
    feedback = (
        db.query(KbArticleFeedback)
        .filter(KbArticleFeedback.id == feedback_id, KbArticleFeedback.tenant_id == tenant_id)
        .first()
    )
    if not feedback:
        logger.info(
            "KB article feedback not found: tenant_id=%s, feedback_id=%s",
            tenant_id,
            feedback_id,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return feedback


def delete_kb_article_feedback(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    feedback_id: uuid.UUID,
    deleted_by: str,
) -> None:
    """Delete a feedback entry (admin only) and publish a deleted event."""
    feedback = get_kb_article_feedback(db, tenant_id=tenant_id, feedback_id=feedback_id)
    db.delete(feedback)
    commit_or_raise(db, action="delete KB article feedback")
    KbArticleFeedbackProducer.send_kb_article_feedback_deleted(
        tenant_id=tenant_id, deleted_dt=datetime.utcnow().isoformat()
    )