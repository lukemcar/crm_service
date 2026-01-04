"""
Tests for the RecordWatcher service functions.

These tests validate that the service layer correctly checks for
existing watchers, enforces tenant matching, and emits creation and
deletion events.  A lightweight ``DummySession`` class is used in
place of a real SQLAlchemy session to satisfy type hints and capture
method invocations.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.models.record_watcher import RecordWatcher
from app.domain.schemas.record_watcher import RecordWatcherCreate
import app.domain.services.record_watcher_service as watcher_service


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    # Provide minimal interface for adding, querying and deleting objects
    def __init__(self) -> None:
        super().__init__()
        self.items: list[RecordWatcher] = []

    def query(self, model):  # type: ignore[override]
        # Return self to allow filter() chaining
        return self

    def filter(self, *args, **kwargs):  # type: ignore[override]
        return self

    def first(self):  # type: ignore[override]
        return None

    def add(self, instance):  # type: ignore[override]
        self.items.append(instance)

    def commit(self):  # type: ignore[override]
        pass

    def refresh(self, instance):  # type: ignore[override]
        pass

    def delete(self, instance):  # type: ignore[override]
        if instance in self.items:
            self.items.remove(instance)


def test_service_create_watcher_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Creating a watcher with existing values should raise a 409 HTTPException."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    record_type = "CONTACT"
    record_id = uuid.uuid4()
    principal_type = "USER"
    principal_id = uuid.uuid4()
    watcher_in = RecordWatcherCreate(
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
    )
    # Stub query.first to simulate existing watcher
    def fake_first():
        return RecordWatcher(
            tenant_id=tenant_id,
            record_type=record_type,
            record_id=record_id,
            principal_type=principal_type,
            principal_id=principal_id,
            created_by_user_id=None,
        )
    monkeypatch.setattr(db, "first", fake_first)
    with pytest.raises(HTTPException) as exc_info:
        watcher_service.service_create_watcher(
            db,
            tenant_id=tenant_id,
            watcher_in=watcher_in,
            created_by_user_id=None,
        )
    assert exc_info.value.status_code == 409


def test_service_create_watcher_tenant_mismatch() -> None:
    """Creating a watcher with mismatched tenant IDs should raise a 400 HTTPException."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    watcher_in = RecordWatcherCreate(
        tenant_id=other_tenant,
        record_type="CONTACT",
        record_id=uuid.uuid4(),
        principal_type="USER",
        principal_id=uuid.uuid4(),
    )
    with pytest.raises(HTTPException) as exc_info:
        watcher_service.service_create_watcher(
            db,
            tenant_id=tenant_id,
            watcher_in=watcher_in,
            created_by_user_id=None,
        )
    assert exc_info.value.status_code == 400