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
from app.domain.schemas.list_membership import ListMembershipCreate


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