"""Service layer for Association operations.

Associations enable arbitrary relationships between any two CRM
entities.  Each association is scoped to a tenant and records both
sides of the link along with an optional association type.  Updates are
not supported; clients should delete and recreate associations as
needed.

This module follows the canonical service pattern established for the
CRM.  All database writes are committed via ``commit_or_raise`` to
centralize error handling, and events are emitted only after a
successful commit.  Audit fields (``created_by``) are strings derived
from the ``X-User`` header.  The service exposes tenant‑scoped
functions for CRUD operations along with admin variants that allow
cross‑tenant listing.
"""

from __future__ import annotations

import uuid
from typing import Iterable, List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.association import Association
from app.domain.schemas.association import AssociationCreate, AssociationRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.association_producer import AssociationMessageProducer

import logging

logger = logging.getLogger("association_service")


def _association_snapshot(association: Association) -> Dict[str, Any]:
    """Return a dictionary snapshot of the association for event payloads."""
    read_model = AssociationRead.model_validate(association, from_attributes=True)
    return read_model.model_dump()


def list_associations(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[Association], int]:
    """Return a list of associations for a given tenant with optional pagination."""
    query = db.query(Association).filter(Association.tenant_id == tenant_id)
    total = query.count()
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    items = query.all()
    return items, total


def get_association(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    association_id: uuid.UUID,
) -> Association:
    """Fetch a single association by ID within the tenant.

    Raises HTTP 404 if the association does not exist or does not belong to the tenant.
    """
    association: Optional[Association] = (
        db.query(Association)
        .filter(Association.id == association_id, Association.tenant_id == tenant_id)
        .first()
    )
    if association is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Association not found",
        )
    return association


def create_association(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    association_in: AssociationCreate,
    created_user: str,
) -> Association:
    """Create a new association for the tenant.

    All writes are committed via ``commit_or_raise`` and the creation event is
    published after a successful commit.
    """
    association = Association(
        tenant_id=tenant_id,
        from_object_type=association_in.from_object_type,
        from_object_id=association_in.from_object_id,
        to_object_type=association_in.to_object_type,
        to_object_id=association_in.to_object_id,
        association_type=association_in.association_type,
        created_by=created_user,
    )
    db.add(association)
    commit_or_raise(db, refresh=association, action="create association")
    snapshot = _association_snapshot(association)
    try:
        AssociationMessageProducer.send_association_created(
            tenant_id=tenant_id,
            payload=snapshot,
        )
    except Exception:
        logger.exception(
            "Failed to publish association.created event tenant_id=%s association_id=%s",
            tenant_id,
            association.id,
        )
    return association


def delete_association(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    association_id: uuid.UUID,
) -> None:
    """Delete the specified association and publish a deletion event."""
    association = get_association(db, tenant_id=tenant_id, association_id=association_id)
    db.delete(association)
    commit_or_raise(db, action="delete association")
    try:
        AssociationMessageProducer.send_association_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        logger.exception(
            "Failed to publish association.deleted event tenant_id=%s association_id=%s",
            tenant_id,
            association_id,
        )


def service_list_associations(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[Association], int]:
    """Admin variant of list_associations that optionally scopes by tenant.

    If ``tenant_id`` is ``None``, associations across all tenants are returned.
    """
    query = db.query(Association)
    if tenant_id is not None:
        query = query.filter(Association.tenant_id == tenant_id)
    total = query.count()
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    items = query.all()
    return items, total


def service_create_association(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    association_in: AssociationCreate,
    created_user: str,
) -> Association:
    """Admin variant of create_association.  Delegates to the tenant‑scoped variant."""
    return create_association(
        db=db,
        tenant_id=tenant_id,
        association_in=association_in,
        created_user=created_user,
    )


def service_delete_association(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    association_id: uuid.UUID,
) -> None:
    """Admin variant of delete_association.  Delegates to the tenant‑scoped variant."""
    delete_association(
        db=db,
        tenant_id=tenant_id,
        association_id=association_id,
    )