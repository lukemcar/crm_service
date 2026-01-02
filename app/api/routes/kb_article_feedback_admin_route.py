"""
Admin‑scoped endpoints for knowledge base article feedback.

This router exposes endpoints to list, create, retrieve and delete feedback
entries across tenants.  Administrators specify the tenant via query
parameters when retrieving or modifying feedback.  Audit fields are
populated from the ``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_article_feedback import (
    AdminCreateKbArticleFeedback,
    KbArticleFeedbackOut,
)
from app.domain.services import kb_article_feedback_service


router = APIRouter(
    prefix="/admin/kb_article_feedback",
    tags=["Knowledge Base Article Feedback"],
)


@router.get("", response_model=List[KbArticleFeedbackOut])
def list_kb_article_feedback_admin_endpoint(
    tenant_id: Optional[UUID] = Query(
        None, description="If provided, filters feedback by tenant"
    ),
    kb_article_id: Optional[UUID] = Query(
        None, description="If provided, filters feedback by article"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbArticleFeedbackOut]:
    """List knowledge base article feedback across tenants with optional filters."""
    feedback_entries, _ = kb_article_feedback_service.list_kb_article_feedback(
        db,
        tenant_id=tenant_id,
        kb_article_id=kb_article_id,
        limit=limit,
        offset=offset,
    )
    return [KbArticleFeedbackOut.model_validate(f, from_attributes=True) for f in feedback_entries]


@router.post("", response_model=KbArticleFeedbackOut, status_code=status.HTTP_201_CREATED)
def create_kb_article_feedback_admin_endpoint(
    feedback_in: AdminCreateKbArticleFeedback,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbArticleFeedbackOut:
    """Create an article feedback entry via the admin API specifying the tenant."""
    created_user = x_user or "anonymous"
    feedback = kb_article_feedback_service.create_kb_article_feedback(
        db,
        tenant_id=feedback_in.tenant_id,
        request=feedback_in,
        created_by=created_user,
    )
    return KbArticleFeedbackOut.model_validate(feedback, from_attributes=True)


@router.get("/{feedback_id}", response_model=KbArticleFeedbackOut)
def get_kb_article_feedback_admin_endpoint(
    feedback_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the feedback to scope the search"
    ),
    db: Session = Depends(get_db),
) -> KbArticleFeedbackOut:
    """Retrieve an article feedback entry via the admin API."""
    feedback = kb_article_feedback_service.get_kb_article_feedback(
        db,
        tenant_id=tenant_id,
        feedback_id=feedback_id,
    )
    return KbArticleFeedbackOut.model_validate(feedback, from_attributes=True)


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kb_article_feedback_admin_endpoint(
    feedback_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the feedback to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an article feedback entry via the admin API."""
    kb_article_feedback_service.delete_kb_article_feedback(
        db,
        tenant_id=tenant_id,
        feedback_id=feedback_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_article_feedback_admin_endpoint",
    "create_kb_article_feedback_admin_endpoint",
    "get_kb_article_feedback_admin_endpoint",
    "delete_kb_article_feedback_admin_endpoint",
]