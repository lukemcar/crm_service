"""
Tenant‑scoped endpoints for knowledge base article feedback.

This router exposes endpoints to list, create, and retrieve feedback on
knowledge base articles within a tenant.  Feedback entries are append‑only
and cannot be modified via tenant APIs.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_article_feedback import (
    TenantCreateKbArticleFeedback,
    KbArticleFeedbackOut,
)
from app.domain.services import kb_article_feedback_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/kb_articles/{article_id}/feedback",
    tags=["Knowledge Base Article Feedback"],
)


@router.get("", response_model=List[KbArticleFeedbackOut])
def list_kb_article_feedback_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
) -> List[KbArticleFeedbackOut]:
    """List feedback entries for a specific article within a tenant."""
    feedback_entries, _ = kb_article_feedback_service.list_kb_article_feedback(
        db,
        tenant_id=tenant_id,
        kb_article_id=article_id,
    )
    return [KbArticleFeedbackOut.model_validate(f, from_attributes=True) for f in feedback_entries]


@router.post("", response_model=KbArticleFeedbackOut, status_code=status.HTTP_201_CREATED)
def create_kb_article_feedback_tenant_endpoint(
    feedback_in: TenantCreateKbArticleFeedback,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbArticleFeedbackOut:
    """Create a feedback entry for an article within a tenant."""
    created_user = x_user or "anonymous"
    # Ensure path article_id matches body
    if feedback_in.kb_article_id != article_id:
        raise ValueError("Path article_id does not match body kb_article_id")
    feedback = kb_article_feedback_service.create_kb_article_feedback(
        db,
        tenant_id=tenant_id,
        request=feedback_in,
        created_by=created_user,
    )
    return KbArticleFeedbackOut.model_validate(feedback, from_attributes=True)


@router.get("/{feedback_id}", response_model=KbArticleFeedbackOut)
def get_kb_article_feedback_tenant_endpoint(
    tenant_id: UUID = Path(..., description="Tenant ID"),
    article_id: UUID = Path(..., description="Article ID"),
    feedback_id: UUID = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db),
) -> KbArticleFeedbackOut:
    """Retrieve a specific feedback entry within a tenant."""
    feedback = kb_article_feedback_service.get_kb_article_feedback(
        db,
        tenant_id=tenant_id,
        feedback_id=feedback_id,
    )
    return KbArticleFeedbackOut.model_validate(feedback, from_attributes=True)


__all__ = [
    "list_kb_article_feedback_tenant_endpoint",
    "create_kb_article_feedback_tenant_endpoint",
    "get_kb_article_feedback_tenant_endpoint",
]