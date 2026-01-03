"""Tests for the List admin and tenant routes.

These tests verify that the refactored list endpoints delegate to the
service layer with the correct parameters and that audit fields are
populated from the ``X‑User`` header when provided.  A simple
``DummySession`` class is used to satisfy type hints without requiring
a real database connection.  Service functions are monkeypatched to
capture their inputs and return predictable results.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.list import ListCreate, ListUpdate, ListRead
import app.domain.services.list_service as list_service

from app.api.routes.lists_admin_route import (
    list_lists as list_lists_admin,
    create_list as create_list_admin,
    update_list as update_list_admin,
    delete_list as delete_list_admin,
)
from app.api.routes.lists_tenant_route import (
    list_lists as list_lists_tenant,
    create_list as create_list_tenant,
    update_list as update_list_tenant,
    delete_list as delete_list_tenant,
)


class DummySession(Session):
    """Lightweight stand‑in for SQLAlchemy Session to satisfy type hints."""

    pass


def _fake_list_read(
    tenant_id: uuid.UUID,
    list_id: uuid.UUID,
    name: str = "Test List",
    object_type: str = "contact",
    list_type: str = "static",
    created_by: str = "tester",
    updated_by: str = "tester",
) -> ListRead:
    """Construct a ``ListRead`` with common defaults and dynamic timestamps."""
    now = datetime.now(timezone.utc)
    return ListRead(
        id=list_id,
        tenant_id=tenant_id,
        name=name,
        object_type=object_type,
        list_type=list_type,
        filter_definition=None,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


def test_list_lists_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should forward filters and pagination to the service."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_lists: List[ListRead] = [_fake_list_read(tenant_id, uuid.uuid4())]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_lists, total

    monkeypatch.setattr(list_service, "service_list_lists", fake_list)

    result = list_lists_admin(
        tenant_id=tenant_id,
        name="Search",
        object_type="contact",
        list_type="static",
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["name"] == "Search"
    assert captured["object_type"] == "contact"
    assert captured["list_type"] == "static"
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_lists)


def test_create_list_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should pass through ``X‑User`` to the service layer."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ListCreate(name="New List", object_type="contact", list_type="static")
    fake_list = _fake_list_read(
        tenant_id=tenant_id,
        list_id=uuid.uuid4(),
        name=payload.name,
        object_type=payload.object_type,
        list_type=payload.list_type,
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_list

    monkeypatch.setattr(list_service, "service_create_list", fake_create)

    result = create_list_admin(
        tenant_id=tenant_id,
        list_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_in"] == payload
    assert captured["created_user"] == "creator"
    assert result.id == fake_list.id


def test_update_list_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin update endpoint should forward the modified user and list ID."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ListUpdate(name="Updated Name")
    fake_list = _fake_list_read(
        tenant_id=tenant_id,
        list_id=list_id,
        name=payload.name or "Test",
    )
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_list

    monkeypatch.setattr(list_service, "service_update_list", fake_update)

    result = update_list_admin(
        tenant_id=tenant_id,
        list_id=list_id,
        list_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert captured["list_in"] == payload
    assert captured["modified_user"] == "editor"
    assert result.id == fake_list.id


def test_delete_list_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should pass list ID and tenant ID to the service layer."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(list_service, "service_delete_list", fake_delete)

    result = delete_list_admin(
        tenant_id=tenant_id,
        list_id=list_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    # Delete returns a Response with status 204
    assert result.status_code == 204


def test_list_lists_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant list endpoint should forward optional filters and pagination."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_lists: List[ListRead] = [_fake_list_read(tenant_id, uuid.uuid4())]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_lists, total

    monkeypatch.setattr(list_service, "service_list_lists", fake_list)

    result = list_lists_tenant(
        tenant_id=tenant_id,
        name=None,
        object_type=None,
        list_type=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["name"] is None
    assert captured["object_type"] is None
    assert captured["list_type"] is None
    assert captured["limit"] is None
    assert captured["offset"] is None
    assert result.total == total
    assert len(result.items) == len(fake_lists)


def test_create_list_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant create endpoint should forward ``X‑User`` to the service layer."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ListCreate(name="Tenant List", object_type="contact", list_type="static")
    fake_list = _fake_list_read(
        tenant_id=tenant_id,
        list_id=uuid.uuid4(),
        name=payload.name,
        object_type=payload.object_type,
        list_type=payload.list_type,
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_list

    monkeypatch.setattr(list_service, "service_create_list", fake_create)

    result = create_list_tenant(
        tenant_id=tenant_id,
        list_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_in"] == payload
    assert captured["created_user"] == "creator"
    assert result.id == fake_list.id


def test_update_list_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant update endpoint should forward the modified user and list ID."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ListUpdate(name="Tenant Updated")
    fake_list = _fake_list_read(
        tenant_id=tenant_id,
        list_id=list_id,
        name=payload.name or "Test",
    )
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_list

    monkeypatch.setattr(list_service, "service_update_list", fake_update)

    result = update_list_tenant(
        tenant_id=tenant_id,
        list_id=list_id,
        list_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert captured["list_in"] == payload
    assert captured["modified_user"] == "editor"
    assert result.id == fake_list.id


def test_delete_list_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant delete endpoint should pass list ID to the service layer."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(list_service, "service_delete_list", fake_delete)

    result = delete_list_tenant(
        tenant_id=tenant_id,
        list_id=list_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert result.status_code == 204