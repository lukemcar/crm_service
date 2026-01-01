"""
Service layer for Knowledge Base Section entities.

This module implements CRUD operations for knowledge base sections.  Sections
belong to categories and tenants.  The service enforces tenant scoping,
handles transactions via ``commit_or_raise`` and emits events through the
message producer after successful mutations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.kb_section import KbSection
from app.domain.schemas.kb_section import (
    TenantCreateKbSection,
    AdminCreateKbSection,
    KbSectionUpdate,
)
from app.domain.schemas.events.kb_section_event import KbSectionDelta
from app.messaging.producers.kb_section_producer import (
    KbSectionMessageProducer as KbSectionProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("kb_section_service")


def _snapshot(section: KbSection) -> Dict[str, Any]:
    return {
        "id": section.id,
        "tenant_id": section.tenant_id,
        "kb_category_id": section.kb_category_id,
        "name": section.name,
        "description": section.description,
        "is_active": section.is_active,
        "created_at": section.created_at.isoformat() if section.created_at else None,
        "updated_at": section.updated_at.isoformat() if section.updated_at else None,
        "created_by": section.created_by,
        "updated_by": section.updated_by,
    }


def _compute_delta(section: KbSection, updates: Dict[str, Any]) -> KbSectionDelta:
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(section, field)
        if current != value:
            changed[field] = value
    return KbSectionDelta(base_fields=changed or None)


def list_kb_sections(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    kb_category_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[KbSection], int]:
    """List sections with optional tenant and category filters."""
    logger.debug(
        "Listing KB sections: tenant_id=%s, category_id=%s, limit=%s, offset=%s",
        tenant_id,
        kb_category_id,
        limit,
        offset,
    )
    query = db.query(KbSection)
    if tenant_id:
        query = query.filter(KbSection.tenant_id == tenant_id)
    if kb_category_id:
        query = query.filter(KbSection.kb_category_id == kb_category_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(KbSection.created_at.desc())
    return query.all(), total


def create_kb_section(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateKbSection | AdminCreateKbSection,
    created_by: str,
) -> KbSection:
    """Create a section and publish an event."""
    logger.debug(
        "Creating KB section: tenant_id=%s, category_id=%s, name=%s",
        tenant_id,
        request.kb_category_id,
        request.name,
    )
    section = KbSection(
        tenant_id=tenant_id,
        kb_category_id=request.kb_category_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active if request.is_active is not None else True,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(section)
    commit_or_raise(db, refresh=section, action="create KB section")
    snapshot = _snapshot(section)
    KbSectionProducer.send_kb_section_created(tenant_id=tenant_id, payload=snapshot)
    return section


def get_kb_section(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    section_id: uuid.UUID,
) -> KbSection:
    """Retrieve a section by ID within a tenant."""
    section = (
        db.query(KbSection)
        .filter(KbSection.id == section_id, KbSection.tenant_id == tenant_id)
        .first()
    )
    if not section:
        logger.info(
            "KB section not found: tenant_id=%s, section_id=%s", tenant_id, section_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


def update_kb_section(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    section_id: uuid.UUID,
    request: KbSectionUpdate,
    updated_by: str,
) -> KbSection:
    """Update a section and publish a delta event if changed."""
    section = get_kb_section(db, tenant_id=tenant_id, section_id=section_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "description", "is_active"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(section, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(section, field, value)
        section.updated_by = updated_by
        section.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=section, action="update KB section")
        snapshot = _snapshot(section)
        KbSectionProducer.send_kb_section_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return section


def delete_kb_section(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    section_id: uuid.UUID,
    deleted_by: str,
) -> None:
    """Delete a section and publish a deleted event."""
    section = get_kb_section(db, tenant_id=tenant_id, section_id=section_id)
    db.delete(section)
    commit_or_raise(db, action="delete KB section")
    KbSectionProducer.send_kb_section_deleted(
        tenant_id=tenant_id, deleted_dt=datetime.utcnow().isoformat()
    )