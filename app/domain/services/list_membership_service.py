"""Service layer for ListMembership operations.

This module provides helper functions to manage memberships in lists.
Memberships link lists to individual CRM records (contacts, companies,
deals, etc.).  Functions here ensure list scope via list_id; additional
tenant scoping should be enforced by callers when necessary.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.list_membership import ListMembership
from app.domain.schemas.list_membership import ListMembershipCreate, ListMembershipRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.list_membership_producer import ListMembershipMessageProducer
from fastapi import HTTPException, status
from typing import Tuple, List as TypingList, Dict, Any, Optional


def list_memberships(db: Session, list_id: uuid.UUID) -> Iterable[ListMembership]:
    """Return all memberships for a given list."""
    return db.query(ListMembership).filter(ListMembership.list_id == list_id).all()


def get_membership(db: Session, membership_id: uuid.UUID) -> Optional[ListMembership]:
    """Fetch a single membership by ID."""
    return db.query(ListMembership).filter(ListMembership.id == membership_id).first()


def create_membership(
    db: Session,
    user_id: Optional[uuid.UUID],
    membership_in: ListMembershipCreate,
) -> ListMembership:
    """Create a new membership record.

    Caller must ensure the referenced list belongs to the correct tenant and
    that the member_id corresponds to a valid record of member_type.
    """
    membership = ListMembership(
        list_id=membership_in.list_id,
        member_id=membership_in.member_id,
        member_type=membership_in.member_type,
        created_by=user_id,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def delete_membership(db: Session, membership: ListMembership) -> None:
    """Delete the specified membership."""
    db.delete(membership)
    db.commit()


# ---------------------------------------------------------------------------
# New service functions using the canonical pattern
# ---------------------------------------------------------------------------

def _membership_snapshot(membership: ListMembership) -> Dict[str, Any]:
    """
    Create a snapshot dictionary of a membership for event payloads.

    Uses the ``ListMembershipRead`` Pydantic model with ``from_attributes=True`` to
    ensure that all consumer‑visible fields are captured.  The returned
    dictionary can be used as the payload for created events.
    """
    read_model = ListMembershipRead.model_validate(membership, from_attributes=True)
    return read_model.model_dump()


def service_list_memberships(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID],
    list_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[ListMembership], int]:
    """
    List memberships for a given list with optional pagination.

    If ``tenant_id`` is provided, the caller should validate that the list
    belongs to the tenant before invoking this function.  This function
    simply returns memberships for the specified list and does not perform
    tenant validation.
    """
    query = db.query(ListMembership).filter(ListMembership.list_id == list_id)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_get_membership(
    db: Session,
    *,
    membership_id: uuid.UUID,
) -> ListMembership:
    """
    Retrieve a membership by ID.

    Raises ``HTTPException`` with status 404 if not found.
    """
    membership = db.query(ListMembership).filter(ListMembership.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    return membership


def service_create_membership(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    list_id: uuid.UUID,
    membership_in: ListMembershipCreate,
    created_user: str,
) -> ListMembership:
    """
    Create a new membership and emit a ``list_membership.created`` event.

    The caller must ensure the referenced list belongs to the tenant and that
    the ``member_id`` corresponds to a valid record of ``member_type``.
    The ``list_id`` in ``membership_in`` is ignored and overwritten with
    the path parameter to avoid cross‑list associations.
    """
    membership = ListMembership(
        list_id=list_id,
        member_id=membership_in.member_id,
        member_type=membership_in.member_type,
        created_by=created_user,
    )
    db.add(membership)
    commit_or_raise(db, refresh=membership)
    # Emit event
    try:
        payload = _membership_snapshot(membership)
        ListMembershipMessageProducer.send_membership_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        pass
    return membership


def service_delete_membership(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    membership_id: uuid.UUID,
    deleted_user: Optional[str] = None,
) -> None:
    """
    Delete a membership and emit a ``list_membership.deleted`` event.

    The caller should validate that the membership belongs to a list
    within the tenant before invoking this function.
    """
    membership = service_get_membership(db, membership_id=membership_id)
    db.delete(membership)
    commit_or_raise(db)
    try:
        ListMembershipMessageProducer.send_membership_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass