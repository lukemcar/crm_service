"""
Tests for the Record Watcher admin and tenant routes.

These tests validate that the new record watcher endpoints call the
appropriate service functions with the correct parameters and handle
audit headers.  They follow the same patterns as the list membership
tests.  A ``DummySession`` class stands in for a real SQLAlchemy session.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.record_watcher import (
    RecordWatcherCreate,
    RecordWatcherRead,
)
import app.domain.services.record_watcher_service as watcher_service

from app.api.routes.record_watchers_admin_route import (
    list_watchers_for_record as list_watchers_admin_record,
    create_watcher_for_record as create_watcher_admin,
    delete_watcher_for_record as delete_watcher_admin,
    list_watchers_for_principal as list_watchers_admin_principal,
)
from app.api.routes.record_watchers_tenant_route import (
    list_watchers as list_watchers_tenant,
    create_watcher as create_watcher_tenant,
    delete_watcher as delete_watcher_tenant,
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
    created_by: str = "tester",
) -> RecordWatcherRead:
    """Construct a ``RecordWatcherRead`` with sensible defaults."""
    now = datetime.now(timezone.utc)
    return RecordWatcherRead(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        created_at=now,
        created_by_user_id=created_by,
    )


def test_list_watchers_admin_record_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint (record scope) should pass parameters to the service."""
    tenant_id = uuid.uuid4()
    record_id = uuid.uuid4()
    record_type = "contact"
    fake_db = DummySession()
    fake_watchers: List[RecordWatcherRead] = [
        _fake_watcher_read(tenant_id, record_type, record_id, "user", uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_watchers, total

    monkeypatch.setattr(watcher_service, "service_list_watchers_by_record", fake_list)

    result = list_watchers_admin_record(
        record_type=record_type,
        record_id=record_id,
        tenant_id=tenant_id,
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_watchers)


def test_list_watchers_admin_principal_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint (principal scope) should pass parameters to the service."""
    tenant_id = uuid.uuid4()
    principal_id = uuid.uuid4()
    principal_type = "user"
    fake_db = DummySession()
    fake_watchers: List[RecordWatcherRead] = [
        _fake_watcher_read(tenant_id, "contact", uuid.uuid4(), principal_type, principal_id)
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_watchers, total

    monkeypatch.setattr(watcher_service, "service_list_watchers_by_principal", fake_list)

    result = list_watchers_admin_principal(
        principal_type=principal_type,
        principal_id=principal_id,
        tenant_id=tenant_id,
        limit=10,
        offset=2,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["principal_type"] == principal_type
    assert captured["principal_id"] == principal_id
    assert captured["limit"] == 10
    assert captured["offset"] == 2
    assert result.total == total
    assert len(result.items) == len(fake_watchers)


def test_create_watcher_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should forward audit info and path parameters."""
    tenant_id = uuid.uuid4()
    record_type = "deal"
    record_id = uuid.uuid4()
    fake_db = DummySession()
    payload = RecordWatcherCreate(
        record_type=record_type,
        record_id=record_id,
        principal_type="user",
        principal_id=uuid.uuid4(),
    )
    fake_watcher = _fake_watcher_read(
        tenant_id,
        record_type,
        record_id,
        payload.principal_type,
        payload.principal_id,
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_watcher

    monkeypatch.setattr(watcher_service, "service_create_watcher", fake_create)

    result = create_watcher_admin(
        record_type=record_type,
        record_id=record_id,
        tenant_id=tenant_id,
        watcher_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["watcher_in"] == payload
    assert captured["created_user_id"] == "creator"
    assert result.tenant_id == tenant_id
    assert result.record_id == record_id


def test_delete_watcher_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should pass identifiers to the service."""
    tenant_id = uuid.uuid4()
    record_type = "company"
    record_id = uuid.uuid4()
    principal_type = "group"
    principal_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(watcher_service, "service_delete_watcher", fake_delete)

    result = delete_watcher_admin(
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="deleter",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["principal_type"] == principal_type
    assert captured["principal_id"] == principal_id
    assert captured["deleted_user_id"] == "deleter"
    assert result.status_code == 204


def test_list_watchers_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant list endpoint should forward parameters to the service."""
    tenant_id = uuid.uuid4()
    record_type = "company"
    record_id = uuid.uuid4()
    fake_db = DummySession()
    fake_watchers: List[RecordWatcherRead] = [
        _fake_watcher_read(tenant_id, record_type, record_id, "user", uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_watchers, total

    monkeypatch.setattr(watcher_service, "service_list_watchers_by_record", fake_list)

    result = list_watchers_tenant(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        limit=3,
        offset=1,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["limit"] == 3
    assert captured["offset"] == 1
    assert result.total == total
    assert len(result.items) == len(fake_watchers)


def test_create_watcher_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant create endpoint should forward audit info and path parameters."""
    tenant_id = uuid.uuid4()
    record_type = "contact"
    record_id = uuid.uuid4()
    fake_db = DummySession()
    payload = RecordWatcherCreate(
        record_type=record_type,
        record_id=record_id,
        principal_type="group",
        principal_id=uuid.uuid4(),
    )
    fake_watcher = _fake_watcher_read(
        tenant_id,
        record_type,
        record_id,
        payload.principal_type,
        payload.principal_id,
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_watcher

    monkeypatch.setattr(watcher_service, "service_create_watcher", fake_create)

    result = create_watcher_tenant(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        watcher_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["watcher_in"] == payload
    assert captured["created_user_id"] == "creator"
    assert result.tenant_id == tenant_id
    assert result.record_id == record_id


def test_delete_watcher_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant delete endpoint should pass identifiers to the service."""
    tenant_id = uuid.uuid4()
    record_type = "deal"
    record_id = uuid.uuid4()
    principal_type = "user"
    principal_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(watcher_service, "service_delete_watcher", fake_delete)

    result = delete_watcher_tenant(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        db=fake_db,
        x_user="deleter",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["record_type"] == record_type
    assert captured["record_id"] == record_id
    assert captured["principal_type"] == principal_type
    assert captured["principal_id"] == principal_id
    assert captured["deleted_user_id"] == "deleter"
    assert result.status_code == 204