"""
Service layer for RecordWatcher operations.

This module encapsulates business logic for managing record watchers.
Watchers link principals (users or groups) to CRM records, enabling
subscriptions to record lifecycle events.  Functions defined here
ensure proper creation and deletion semantics, commit handling, and
event publication.  Consumers of this service should perform any
necessary authorization and validation (e.g. verifying that the record
exists and the principal has access) before invoking these functions.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, Optional, Tuple, List as TypingList

from sqlalchemy.orm import Session

from app.domain.models.record_watcher import RecordWatcher
from app.domain.schemas.record_watcher import RecordWatcherCreate, RecordWatcherRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.record_watcher_producer import RecordWatcherMessageProducer
from fastapi import HTTPException, status


def _watcher_snapshot(watcher: RecordWatcher) -> Dict[str, Any]:
    """
    Create a snapshot dictionary of a record watcher for event payloads.

    Uses the ``RecordWatcherRead`` Pydantic model with ``from_attributes=True`` to
    ensure that all consumer‑visible fields are captured.  The returned
    dictionary can be used as the payload for created events.
    """
    read_model = RecordWatcherRead.model_validate(watcher, from_attributes=True)
    return read_model.model_dump()


def service_list_watchers_by_record(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    record_type: str,
    record_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[RecordWatcher], int]:
    """
    List watchers for a given record.

    The caller should validate that the record belongs to the tenant and
    exists before invoking this function.  Returns a tuple of the
    resulting watcher objects and the total count for pagination.
    """
    query = db.query(RecordWatcher).filter(
        RecordWatcher.tenant_id == tenant_id,
        RecordWatcher.record_type == record_type,
        RecordWatcher.record_id == record_id,
    )
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_list_watchers_by_principal(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    principal_type: str,
    principal_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[RecordWatcher], int]:
    """
    List watchers for a given principal.

    Returns a tuple of watchers and total count.  The caller is responsible
    for validating that the principal belongs to the tenant.
    """
    query = db.query(RecordWatcher).filter(
        RecordWatcher.tenant_id == tenant_id,
        RecordWatcher.principal_type == principal_type,
        RecordWatcher.principal_id == principal_id,
    )
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
    record_type: str,
    record_id: uuid.UUID,
    watcher_in: RecordWatcherCreate,
    created_user_id: str,
) -> RecordWatcher:
    """
    Create a new record watcher and emit a ``record_watcher.created`` event.

    The caller must ensure the referenced record exists and belongs to
    the tenant.  The ``record_type`` and ``record_id`` parameters take
    precedence over the values in ``watcher_in`` to avoid cross‑record
    associations.
    """
    watcher = RecordWatcher(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=watcher_in.principal_type,
        principal_id=watcher_in.principal_id,
        created_by_user_id=created_user_id,
    )
    db.add(watcher)
    commit_or_raise(db, refresh=watcher)
    # Emit event after commit
    try:
        payload = _watcher_snapshot(watcher)
        RecordWatcherMessageProducer.send_watcher_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        # suppress messaging errors; classification done elsewhere
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
    deleted_user_id: Optional[str] = None,
) -> None:
    """
    Delete a record watcher and emit a ``record_watcher.deleted`` event.

    Raises HTTP 404 if the watcher does not exist.  The caller should
    ensure tenant/record/principal context validity before invoking.
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
    try:
        RecordWatcherMessageProducer.send_watcher_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass
    return None