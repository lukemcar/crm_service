"""
Tests for the Record Watcher admin routes.

These tests ensure that the admin endpoints for record watchers call
the appropriate service functions with the correct parameters and
propagate audit identifiers from headers.  Dummy stubs are used in
place of real database sessions and service implementations.
"""

from __future__ import annotations

import uuid
from typing import Optional, Tuple, List, Dict

import pytest
from sqlalchemy.orm import Session

from app.domain.models.record_watcher import RecordWatcher
from app.domain.schemas.record_watcher import RecordWatcherCreate, RecordWatcherRead
import app.domain.services.record_watcher_service as watcher_service

from app.api.routes.record_watchers_admin_route import (
    list_watchers_for_record,
    create_watcher_for_record,
    delete_watcher,
)


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""
    pass


def _fake_watcher_read(
    tenant_id: uuid.UUID,
    record_type: str,
    record_id: uuid.UUID,
    principal_type: str,
    principal_id: uuid.UUID,
    created_by_user_id: Optional[uuid.UUID] = None,
) -> RecordWatcherRead:
    return RecordWatcherRead(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        created_at=uuid.uuid1().time,  # use unique timestamp
        created_by_user_id=created_by_user_id,
    )


def test_admin_list_watchers_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should pass record and tenant IDs and pagination to the service."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    record_type = "CONTACT"
    record_id = uuid.uuid4()
    limit = 10
    offset = 0
    fake_watchers: List[RecordWatcherRead] = [
        _fake_watcher_read(tenant_id, record_type, record_id, "USER", uuid.uuid4())
    ]
    total = 1
    captured: Dict[str, object] = {}

    def fake_list(db, **kwargs) -> Tuple[List[RecordWatcher], int]:
        captured["db"] = db
        captured.update(kwargs)
        return fake_watchers, total

    monkeypatch.setattr(watcher_service, "service_list_watchers_by_record", fake_list)

    result = list_watchers_for_record(
        record_type=record_type,
        record_id=record_id,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["tenant_id"] == tenant_id
    assert captured["limit"] == limit
    assert captured["offset"] == offset
    assert result.total == total
    assert len(result.items) == len(fake_watchers)


def test_admin_create_watcher_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should forward tenant and record identifiers and audit user ID."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    record_type = "DEAL"
    record_id = uuid.uuid4()
    principal_type = "GROUP"
    principal_id = uuid.uuid4()
    watcher_in = RecordWatcherCreate(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
    )
    fake_watcher = _fake_watcher_read(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        created_by_user_id=None,
    )
    captured: Dict[str, object] = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_watcher

    monkeypatch.setattr(watcher_service, "service_create_watcher", fake_create)

    result = create_watcher_for_record(
        record_type=record_type,
        record_id=record_id,
        tenant_id=tenant_id,
        watcher_in=watcher_in,
        x_user_id=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    # The watcher_in in the captured dict has overwritten values; ensure they match path parameters
    assert captured["watcher_in"].tenant_id == tenant_id
    assert captured["watcher_in"].record_type == record_type
    assert captured["watcher_in"].record_id == record_id
    assert result.record_type == record_type
    assert result.record_id == record_id


def test_admin_delete_watcher_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should forward tenant, record and principal identifiers."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    record_type = "LEAD"
    record_id = uuid.uuid4()
    principal_type = "USER"
    principal_id = uuid.uuid4()
    captured: Dict[str, object] = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(watcher_service, "service_delete_watcher", fake_delete)

    response = delete_watcher(
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        tenant_id=tenant_id,
        x_user_id=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["principal_type"] == principal_type
    assert captured["principal_id"] == principal_id
    assert response.status_code == 204