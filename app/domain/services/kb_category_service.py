"""
Service layer for Knowledge Base Category entities.

This module implements CRUD operations for the knowledge base category domain.
Categories group sections and articles.  The service enforces tenant scoping,
handles database transactions via ``commit_or_raise`` and emits events
through the message producer after successful mutations.  Listing
operations support pagination.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.kb_category import KbCategory
from app.domain.schemas.kb_category import (
    TenantCreateKbCategory,
    AdminCreateKbCategory,
    KbCategoryUpdate,
)
from app.domain.schemas.events.kb_category_event import KbCategoryDelta
from app.messaging.producers.kb_category_producer import (
    KbCategoryMessageProducer as KbCategoryProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("kb_category_service")


def _snapshot(category: KbCategory) -> Dict[str, Any]:
    """Return a dictionary representation of a KbCategory suitable for event payloads."""
    return {
        "id": category.id,
        "tenant_id": category.tenant_id,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None,
        "created_by": category.created_by,
        "updated_by": category.updated_by,
    }


def _compute_delta(category: KbCategory, updates: Dict[str, Any]) -> KbCategoryDelta:
    """Compute the delta for updated base fields on a KbCategory."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(category, field)
        if current != value:
            changed[field] = value
    return KbCategoryDelta(base_fields=changed or None)


def list_kb_categories(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[KbCategory], int]:
    """List knowledge base categories with optional tenant scoping and pagination."""
    logger.debug(
        "Listing KB categories: tenant_id=%s, limit=%s, offset=%s",
        tenant_id,
        limit,
        offset,
    )
    query = db.query(KbCategory)
    if tenant_id:
        query = query.filter(KbCategory.tenant_id == tenant_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(KbCategory.created_at.desc())
    return query.all(), total


def create_kb_category(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateKbCategory | AdminCreateKbCategory,
    created_by: str,
) -> KbCategory:
    """Create a knowledge base category and publish a created event."""
    logger.debug(
        "Creating KB category: tenant_id=%s, name=%s",
        tenant_id,
        request.name,
    )
    category = KbCategory(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active if request.is_active is not None else True,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(category)
    commit_or_raise(db, refresh=category, action="create KB category")
    snapshot = _snapshot(category)
    KbCategoryProducer.send_kb_category_created(tenant_id=tenant_id, payload=snapshot)
    return category


def get_kb_category(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    category_id: uuid.UUID,
) -> KbCategory:
    """Retrieve a category by ID within a tenant."""
    category = (
        db.query(KbCategory)
        .filter(KbCategory.id == category_id, KbCategory.tenant_id == tenant_id)
        .first()
    )
    if not category:
        logger.info(
            "KB category not found: tenant_id=%s, category_id=%s", tenant_id, category_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def update_kb_category(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    category_id: uuid.UUID,
    request: KbCategoryUpdate,
    updated_by: str,
) -> KbCategory:
    """Update an existing category and publish an updated event if changed."""
    category = get_kb_category(db, tenant_id=tenant_id, category_id=category_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "description", "is_active"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(category, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(category, field, value)
        category.updated_by = updated_by
        category.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=category, action="update KB category")
        snapshot = _snapshot(category)
        KbCategoryProducer.send_kb_category_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return category


def delete_kb_category(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    category_id: uuid.UUID,
    deleted_by: str,
) -> None:
    """Delete a category and publish a deleted event."""
    category = get_kb_category(db, tenant_id=tenant_id, category_id=category_id)
    db.delete(category)
    commit_or_raise(db, action="delete KB category")
    KbCategoryProducer.send_kb_category_deleted(tenant_id=tenant_id, deleted_dt=datetime.utcnow().isoformat())