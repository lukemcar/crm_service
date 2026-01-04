"""
Service layer for record watcher operations.

This module provides helper functions to manage record watchers.  A
record watcher associates a principal (user or group) with a CRM record
of a given type.  Functions here perform validation, commit
transactions, and publish events via the messaging layer.  The caller
should supply a SQLAlchemy session and ensure the referenced record
exists in the system.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable, Optional, Tuple, List as TypingList, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.record_watcher import RecordWatcher
from app.domain.schemas.record_watcher import RecordWatcherCreate, RecordWatcherRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.record_watcher_producer import RecordWatcherMessageProducer


def _watcher_snapshot(watcher: RecordWatcher) -> Dict[str, Any]:
    """Create a snapshot dictionary of a watcher for event payloads.

    Uses the ``RecordWatcherRead`` Pydantic model with ``from_attributes=True`` to
    ensure that all consumer‑visible fields are captured.  The returned
    dictionary can be used as the payload for created events.
    """
    read_model = RecordWatcherRead.model_validate(watcher, from_attributes=True)
    return read_model.model_dump()


def service_list_watchers_by_record(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID],
    record_type: str,
    record_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[RecordWatcher], int]:
    """List all watchers for a given record.

    If ``tenant_id`` is provided, the query is restricted to that tenant.
    Returns a tuple of (items, total) where ``items`` is a list of watchers
    and ``total`` is the total number of watchers before pagination.
    """
    query = db.query(RecordWatcher).filter(
        RecordWatcher.record_type == record_type,
        RecordWatcher.record_id == record_id,
    )
    if tenant_id is not None:
        query = query.filter(RecordWatcher.tenant_id == tenant_id)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_list_watchers_by_principal(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID],
    principal_type: str,
    principal_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[RecordWatcher], int]:
    """List all watchers for a given principal (user or group).

    If ``tenant_id`` is provided, the query is restricted to that tenant.
    Returns a tuple of (items, total) similar to ``service_list_watchers_by_record``.
    """
    query = db.query(RecordWatcher).filter(
        RecordWatcher.principal_type == principal_type,
        RecordWatcher.principal_id == principal_id,
    )
    if tenant_id is not None:
        query = query.filter(RecordWatcher.tenant_id == tenant_id)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_create_watcher(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    watcher_in: RecordWatcherCreate,
    created_by_user_id: Optional[uuid.UUID],
) -> RecordWatcher:
    """Create a new record watcher and emit a ``record_watcher.created`` event.

    Raises a 409 conflict if the watcher already exists.  The caller must
    ensure the referenced record and principal exist within the tenant.
    The ``tenant_id`` in ``watcher_in`` must match the provided ``tenant_id``.
    """
    # Ensure the tenant IDs match to prevent cross‑tenant associations
    if watcher_in.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID mismatch")
    # Check for existing watcher
    existing = db.query(RecordWatcher).filter(
        RecordWatcher.tenant_id == tenant_id,
        RecordWatcher.record_type == watcher_in.record_type,
        RecordWatcher.record_id == watcher_in.record_id,
        RecordWatcher.principal_type == watcher_in.principal_type,
        RecordWatcher.principal_id == watcher_in.principal_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Watcher already exists")
    watcher = RecordWatcher(
        tenant_id=tenant_id,
        record_type=watcher_in.record_type,
        record_id=watcher_in.record_id,
        principal_type=watcher_in.principal_type,
        principal_id=watcher_in.principal_id,
        created_by_user_id=created_by_user_id,
    )
    db.add(watcher)
    commit_or_raise(db, refresh=watcher)
    # Emit event
    try:
        payload = _watcher_snapshot(watcher)
        RecordWatcherMessageProducer.send_watcher_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        # Producer exceptions should not abort the request
        pass
    return watcher


def service_delete_watcher(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    record_type: str,
    record_id: uuid.UUID,
    principal_type: str,
    principal_id: uuid.UUID,
    deleted_by_user_id: Optional[uuid.UUID] = None,
) -> None:
    """Delete a record watcher and emit a ``record_watcher.deleted`` event.

    Raises a 404 if the watcher is not found.  The caller should validate
    that the referenced record and principal belong to the tenant.
    """
    watcher = db.query(RecordWatcher).filter(
        RecordWatcher.tenant_id == tenant_id,
        RecordWatcher.record_type == record_type,
        RecordWatcher.record_id == record_id,
        RecordWatcher.principal_type == principal_type,
        RecordWatcher.principal_id == principal_id,
    ).first()
    if not watcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watcher not found")
    db.delete(watcher)
    commit_or_raise(db)
    # Emit event
    try:
        RecordWatcherMessageProducer.send_watcher_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass
