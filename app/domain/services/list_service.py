"""Service layer for List operations.

Lists (or segments) group CRM records of a given type.  This module
provides CRUD functions for lists, scoped by tenant.  Membership
management is handled separately in the list_membership_service.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.list import List
from app.domain.schemas.list import ListCreate, ListUpdate


def list_lists(db: Session, tenant_id: uuid.UUID) -> Iterable[List]:
    """Return all lists for the given tenant."""
    return db.query(List).filter(List.tenant_id == tenant_id).all()


def get_list(db: Session, list_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[List]:
    """Fetch a single list by ID within the tenant."""
    return (
        db.query(List)
        .filter(List.id == list_id, List.tenant_id == tenant_id)
        .first()
    )


def create_list(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    list_in: ListCreate,
) -> List:
    """Create a new list for the tenant."""
    lst = List(
        tenant_id=tenant_id,
        name=list_in.name,
        object_type=list_in.object_type,
        list_type=list_in.list_type,
        filter_definition=list_in.filter_definition,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return lst


def update_list(
    db: Session,
    lst: List,
    user_id: Optional[uuid.UUID],
    list_in: ListUpdate,
) -> List:
    """Update an existing list with provided fields."""
    if list_in.name is not None:
        lst.name = list_in.name
    if list_in.object_type is not None:
        lst.object_type = list_in.object_type
    if list_in.list_type is not None:
        lst.list_type = list_in.list_type
    if list_in.filter_definition is not None:
        lst.filter_definition = list_in.filter_definition
    lst.updated_by = user_id
    db.commit()
    db.refresh(lst)
    return lst


def delete_list(db: Session, lst: List) -> None:
    """Delete the specified list."""
    db.delete(lst)
    db.commit()