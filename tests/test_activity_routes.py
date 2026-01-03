"""Tests for the Activity admin and tenant routes.

These tests verify that the new Activity routes delegate to the service layer
with the correct parameters and that audit fields are populated from the
``X-User`` header when provided.  A simple ``DummySession`` type is used
to satisfy type hints without requiring a real database connection.  Service
functions are monkeypatched to capture their inputs and return predictable
results.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.activity import ActivityCreate, ActivityUpdate, ActivityRead
import app.domain.services.activity_service as activity_service

from app.api.routes.activities_admin_route import (
    list_activities_admin,
    create_activity_admin,
    update_activity_admin,
    delete_activity_admin,
)

from app.api.routes.activities_tenant_route import (
    list_activities_endpoint,
    create_activity_endpoint,
    update_activity_endpoint,
    delete_activity_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in so type hints are satisfied without a real DB."""

    pass


def _fake_activity_read(
    tenant_id: uuid.UUID,
    activity_id: uuid.UUID,
    type: str = "note",
    title: Optional[str] = "Test",
    description: Optional[str] = None,
    status: Optional[str] = "open",
    assigned_user_id: Optional[uuid.UUID] = None,
    created_by: str = "tester",
    updated_by: str = "tester",
) -> ActivityRead:
    now = datetime.now(timezone.utc)
    return ActivityRead(
        id=activity_id,
        tenant_id=tenant_id,
        type=type,
        title=title,
        description=description,
        due_date=None,
        status=status,
        assigned_user_id=assigned_user_id,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


# ---------------------------------------------------------------------------
# Admin list
# ---------------------------------------------------------------------------


def test_list_activities_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_activities: List[ActivityRead] = [
        _fake_activity_read(tenant_id=tenant_id, activity_id=uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_service_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_activities, total

    monkeypatch.setattr(activity_service, "service_list_activities", fake_service_list)

    result = list_activities_admin(
        tenant_id=tenant_id,
        type="note",
        status="open",
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["type"] == "note"
    assert captured["status"] == "open"
    assert result.total == total
    # Items are converted to ActivityRead models via model_validate, so compare length
    assert len(result.items) == len(fake_activities)


# ---------------------------------------------------------------------------
# Admin create
# ---------------------------------------------------------------------------


def test_create_activity_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ActivityCreate(type="note", title="Hello")
    fake_activity = _fake_activity_read(
        tenant_id=tenant_id, activity_id=uuid.uuid4(), type=payload.type, title=payload.title
    )
    captured: dict = {}

    def fake_create_activity(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_activity

    monkeypatch.setattr(activity_service, "service_create_activity", fake_create_activity)

    result = create_activity_admin(
        tenant_id=tenant_id,
        activity_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["activity_in"] == payload
    assert captured["created_user"] == "tester"
    # Result is revalidated via model_validate
    assert result.id == fake_activity.id


# ---------------------------------------------------------------------------
# Tenant list
# ---------------------------------------------------------------------------


def test_list_activities_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_activities: List[ActivityRead] = [
        _fake_activity_read(tenant_id=tenant_id, activity_id=uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_activities, total

    monkeypatch.setattr(activity_service, "list_activities", fake_list)

    result = list_activities_endpoint(
        tenant_id=tenant_id,
        type="note",
        status="open",
        limit=10,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["type"] == "note"
    assert captured["status"] == "open"
    assert captured["limit"] == 10
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_activities)


# ---------------------------------------------------------------------------
# Tenant create
# ---------------------------------------------------------------------------


def test_create_activity_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ActivityCreate(type="note", title="Hello")
    fake_activity = _fake_activity_read(
        tenant_id=tenant_id, activity_id=uuid.uuid4(), type=payload.type, title=payload.title
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_activity

    monkeypatch.setattr(activity_service, "create_activity", fake_create)

    result = create_activity_endpoint(
        tenant_id=tenant_id,
        activity_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["activity_in"] == payload
    assert captured["created_user"] == "tester"
    assert result.id == fake_activity.id


# ---------------------------------------------------------------------------
# Admin update and delete
# ---------------------------------------------------------------------------


def test_update_activity_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ActivityUpdate(title="Updated")
    fake_activity = _fake_activity_read(
        tenant_id=tenant_id,
        activity_id=activity_id,
        title=payload.title or "",
    )
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_activity

    monkeypatch.setattr(activity_service, "service_update_activity", fake_update)

    result = update_activity_admin(
        tenant_id=tenant_id,
        activity_id=activity_id,
        activity_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["activity_id"] == activity_id
    assert captured["activity_in"] == payload
    assert captured["modified_user"] == "editor"
    assert result.id == fake_activity.id


def test_delete_activity_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(activity_service, "service_delete_activity", fake_delete)

    result = delete_activity_admin(
        tenant_id=tenant_id,
        activity_id=activity_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["activity_id"] == activity_id
    # delete endpoints return None
    assert result is None


# ---------------------------------------------------------------------------
# Tenant update and delete
# ---------------------------------------------------------------------------


def test_update_activity_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ActivityUpdate(title="Updated")
    fake_activity = _fake_activity_read(
        tenant_id=tenant_id,
        activity_id=activity_id,
        title=payload.title or "",
    )
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_activity

    monkeypatch.setattr(activity_service, "update_activity", fake_update)

    result = update_activity_endpoint(
        tenant_id=tenant_id,
        activity_id=activity_id,
        activity_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["activity_id"] == activity_id
    assert captured["activity_in"] == payload
    assert captured["modified_user"] == "editor"
    assert result.id == fake_activity.id


def test_delete_activity_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(activity_service, "delete_activity", fake_delete)

    result = delete_activity_endpoint(
        tenant_id=tenant_id,
        activity_id=activity_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["activity_id"] == activity_id
    assert result is None
