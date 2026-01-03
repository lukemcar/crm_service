"""Service layer for List operations.

Lists (or segments) group CRM records of a given type.  This module
provides CRUD functions for lists, scoped by tenant.  Membership
management is handled separately in the list_membership_service.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional, Tuple, List as TypingList, Dict, Any

from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.domain.models.list import List
from app.domain.schemas.list import ListCreate, ListUpdate, ListRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.list_producer import ListMessageProducer


def list_lists(db: Session, tenant_id: uuid.UUID) -> Iterable[List]:  # pragma: no cover
    """
    Return all lists for the given tenant.

    This function is retained for backwards compatibility with legacy routes.
    New callers should use :func:`service_list_lists` instead, which
    provides optional filtering and pagination.
    """
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
) -> List:  # pragma: no cover
    """
    Legacy create function retained for backward compatibility.

    New code should call :func:`service_create_list` which uses
    ``commit_or_raise`` and emits events.
    """
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
) -> List:  # pragma: no cover
    """
    Legacy update function retained for backward compatibility.

    New code should call :func:`service_update_list` which uses
    ``commit_or_raise`` and emits events when changes are detected.
    """
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


# ---------------------------------------------------------------------------
# New service functions using the canonical pattern
# ---------------------------------------------------------------------------

def _list_snapshot(lst: List) -> dict[str, Any]:
    """
    Create a snapshot dictionary of a list for event payloads.

    Uses the ``ListRead`` Pydantic model with ``from_attributes=True`` to
    ensure that all consumer‑visible fields are captured.  The returned
    dictionary can be used as the payload for created and updated events.
    """
    read_model = ListRead.model_validate(lst, from_attributes=True)
    return read_model.model_dump()


def service_list_lists(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    name: Optional[str] = None,
    object_type: Optional[str] = None,
    list_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> tuple[list[List], int]:
    """
    List lists with optional filtering and pagination.

    Parameters
    ----------
    tenant_id : UUID | None
        If provided, results are scoped to this tenant.  If omitted, lists
        across all tenants are returned (admin context only).
    name : str | None
        Case‑insensitive substring filter on the list name.
    object_type : str | None
        Exact match filter on the list's object type.
    list_type : str | None
        Exact match filter on the list's type.
    limit : int | None
        Maximum number of records to return.  If ``None``, no limit is
        applied.
    offset : int | None
        Number of records to skip from the beginning.  If ``None``, no
        offset is applied.

    Returns
    -------
    (list[``List``], int)
        A tuple of the list of ORM instances and the total number of records
        matching the filters (before pagination).
    """
    query = db.query(List)
    if tenant_id is not None:
        query = query.filter(List.tenant_id == tenant_id)
    if name:
        # Case‑insensitive substring match using ILIKE on Postgres or lower/like
        query = query.filter(List.name.ilike(f"%{name}%"))
    if object_type:
        query = query.filter(List.object_type == object_type)
    if list_type:
        query = query.filter(List.list_type == list_type)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_get_list(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    list_id: uuid.UUID,
) -> List:
    """
    Retrieve a single list by ID for a tenant.

    Raises an ``HTTPException`` with status 404 if the list is not found.
    """
    lst = (
        db.query(List)
        .filter(List.id == list_id, List.tenant_id == tenant_id)
        .first()
    )
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )
    return lst


def service_create_list(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    list_in: ListCreate,
    created_user: str,
) -> List:
    """
    Create a new list and emit a ``list.created`` event.

    Parameters
    ----------
    tenant_id : UUID
        Tenant that will own the list.
    list_in : ``ListCreate``
        Pydantic model containing fields for the new list.
    created_user : str
        Identifier of the user creating the list, derived from the ``X-User``
        header.  If not provided, callers should supply a sensible default
        such as ``"anonymous"``.
    """
    lst = List(
        tenant_id=tenant_id,
        name=list_in.name,
        object_type=list_in.object_type,
        list_type=list_in.list_type,
        filter_definition=list_in.filter_definition,
        created_by=created_user,
        updated_by=created_user,
    )
    db.add(lst)
    commit_or_raise(db, refresh=lst)
    # Emit event
    try:
        payload = _list_snapshot(lst)
        ListMessageProducer.send_list_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        # Suppress exceptions from event publishing; transaction already committed
        pass
    return lst


def service_update_list(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    list_id: uuid.UUID,
    list_in: ListUpdate,
    modified_user: str,
) -> List:
    """
    Update an existing list and emit a ``list.updated`` event if changes occur.

    Only fields provided in ``list_in`` are updated.  The caller should
    validate any constraints as necessary prior to invoking this function.
    """
    # Fetch list
    lst = service_get_list(db, tenant_id=tenant_id, list_id=list_id)
    before = _list_snapshot(lst)
    # Apply updates
    if list_in.name is not None:
        lst.name = list_in.name
    if list_in.object_type is not None:
        lst.object_type = list_in.object_type
    if list_in.list_type is not None:
        lst.list_type = list_in.list_type
    if list_in.filter_definition is not None:
        lst.filter_definition = list_in.filter_definition
    lst.updated_by = modified_user
    # Commit and refresh
    commit_or_raise(db, refresh=lst)
    after = _list_snapshot(lst)
    changes = {k: after[k] for k in after.keys() if before.get(k) != after.get(k)}
    if changes:
        try:
            ListMessageProducer.send_list_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=after,
            )
        except Exception:
            pass
    return lst


def service_delete_list(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    list_id: uuid.UUID,
) -> None:
    """
    Delete a list and emit a ``list.deleted`` event.

    Parameters
    ----------
    tenant_id : UUID
        Tenant that owns the list.
    list_id : UUID
        Identifier of the list to delete.
    """
    lst = service_get_list(db, tenant_id=tenant_id, list_id=list_id)
    db.delete(lst)
    commit_or_raise(db)
    try:
        ListMessageProducer.send_list_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass