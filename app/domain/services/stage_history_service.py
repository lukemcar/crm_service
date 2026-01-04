"""
Service layer for stage history operations.

This module provides helper functions to manage stage history records.
Stage history entries capture transitions of CRM entities between
pipeline stages along with metadata such as who performed the change
and when it occurred.  The service functions perform validation,
commit transactions, and return ORM objects for further use.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List as TypingList, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.stage_history import StageHistory
from app.domain.schemas.stage_history import StageHistoryCreate
from app.domain.services.common_service import commit_or_raise


def service_create_stage_history(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    history_in: StageHistoryCreate,
    changed_by_user_id: Optional[uuid.UUID],
) -> StageHistory:
    """Create a new stage history entry.

    Args:
        db: SQLAlchemy session to use for DB operations.
        tenant_id: The tenant ID in the URL path. Must match the tenant in ``history_in``.
        history_in: Pydantic model with stage history creation attributes.
        changed_by_user_id: Optional user identifier from the request header representing
            who initiated the change.

    Returns:
        The newly created StageHistory ORM instance.

    Raises:
        HTTPException: If the tenant ID in the payload does not match the path parameter.
    """
    if history_in.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID mismatch")
    # Construct the StageHistory instance.  changed_at defaults to now if not provided
    history = StageHistory(
        tenant_id=history_in.tenant_id,
        entity_type=history_in.entity_type,
        entity_id=history_in.entity_id,
        pipeline_id=history_in.pipeline_id,
        from_stage_id=history_in.from_stage_id,
        to_stage_id=history_in.to_stage_id,
        changed_at=history_in.changed_at or datetime.utcnow(),
        changed_by_user_id=changed_by_user_id or history_in.changed_by_user_id,
        source=history_in.source,
    )
    db.add(history)
    commit_or_raise(db, refresh=history)
    return history


def service_list_stage_history_by_entity(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID],
    entity_type: str,
    entity_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[StageHistory], int]:
    """List stage history entries for a specific entity.

    Args:
        db: SQLAlchemy session.
        tenant_id: Optional tenant ID for multi‑tenant filtering. If provided,
            the query will include only entries matching this tenant.
        entity_type: The type of the entity (e.g., DEAL, LEAD).
        entity_id: The identifier of the entity whose history is requested.
        limit: Maximum number of entries to return.
        offset: Number of entries to skip for pagination.

    Returns:
        A tuple ``(items, total)`` where ``items`` is the list of StageHistory
        entries and ``total`` is the total count before pagination.
    """
    query = db.query(StageHistory).filter(
        StageHistory.entity_type == entity_type,
        StageHistory.entity_id == entity_id,
    )
    if tenant_id is not None:
        query = query.filter(StageHistory.tenant_id == tenant_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all(), total


def service_list_stage_history_by_pipeline(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID],
    pipeline_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[StageHistory], int]:
    """List stage history entries for a specific pipeline.

    Args:
        db: SQLAlchemy session.
        tenant_id: Optional tenant ID for multi‑tenant filtering.
        pipeline_id: The pipeline whose history entries are requested.
        limit: Maximum number of entries to return.
        offset: Number of entries to skip for pagination.

    Returns:
        A tuple ``(items, total)`` similar to ``service_list_stage_history_by_entity``.
    """
    query = db.query(StageHistory).filter(StageHistory.pipeline_id == pipeline_id)
    if tenant_id is not None:
        query = query.filter(StageHistory.tenant_id == tenant_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return query.all(), total


__all__ = [
    "service_create_stage_history",
    "service_list_stage_history_by_entity",
    "service_list_stage_history_by_pipeline",
]