from __future__ import annotations

import uuid
from typing import Optional, Dict, Any

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.support_view import (
    TenantCreateSupportView,
    SupportViewUpdate,
    SupportViewOut,
)
from app.domain.services import support_view_service

from app.api.routes.support_views_tenant_route import (
    list_support_views_endpoint,
    create_support_view_endpoint,
    update_support_view_endpoint,
    get_support_view_endpoint,
    delete_support_view_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""

    pass


def _fake_support_view_out(
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
    is_active: bool = True,
    filter_definition: Optional[Dict[str, Any]] = None,
    sort_definition: Optional[Dict[str, Any]] = None,
) -> SupportViewOut:
    return SupportViewOut(
        id=view_id,
        tenant_id=tenant_id,
        name=name,
        description=description,
        is_active=is_active,
        filter_definition=filter_definition or {"status": "open"},
        sort_definition=sort_definition,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_support_views_endpoint
# ---------------------------------------------------------------------------


def test_list_support_views_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_views = [
        _fake_support_view_out(
            tenant_id=tenant_id,
            view_id=uuid.uuid4(),
            name="My Open Tickets",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_views, total

    monkeypatch.setattr(support_view_service, "list_support_views", fake_list)

    result = list_support_views_endpoint(
        tenant_id=tenant_id,
        is_active=True,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["is_active"] is True
    assert result.total == total
    assert result.items == fake_views


# ---------------------------------------------------------------------------
# create_support_view_endpoint
# ---------------------------------------------------------------------------


def test_create_support_view_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateSupportView(
        name="High Priority", description="Urgent tickets", is_active=True, filter_definition={"priority": "urgent"}
    )
    fake_view = _fake_support_view_out(
        tenant_id=tenant_id,
        view_id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        is_active=True,
        filter_definition=payload.filter_definition,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_view

    monkeypatch.setattr(support_view_service, "create_support_view", fake_create)

    result = create_support_view_endpoint(
        tenant_id=tenant_id,
        view_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_view


# ---------------------------------------------------------------------------
# update_support_view_endpoint
# ---------------------------------------------------------------------------


def test_update_support_view_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    view_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = SupportViewUpdate(name="Updated Name", description="Updated description")
    fake_view = _fake_support_view_out(
        tenant_id=tenant_id,
        view_id=view_id,
        name="Updated Name",
        description="Updated description",
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_view

    monkeypatch.setattr(support_view_service, "update_support_view", fake_update)

    result = update_support_view_endpoint(
        tenant_id=tenant_id,
        view_id=view_id,
        view_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["view_id"] == view_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_view


# ---------------------------------------------------------------------------
# get_support_view_endpoint
# ---------------------------------------------------------------------------


def test_get_support_view_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    view_id = uuid.uuid4()
    fake_db = DummySession()
    fake_view = _fake_support_view_out(
        tenant_id=tenant_id,
        view_id=view_id,
        name="My View",
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_view

    monkeypatch.setattr(support_view_service, "get_support_view", fake_get)

    result = get_support_view_endpoint(
        tenant_id=tenant_id,
        view_id=view_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["view_id"] == view_id
    assert result == fake_view


# ---------------------------------------------------------------------------
# delete_support_view_endpoint
# ---------------------------------------------------------------------------


def test_delete_support_view_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    view_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(support_view_service, "delete_support_view", fake_delete)

    result = delete_support_view_endpoint(
        tenant_id=tenant_id,
        view_id=view_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["view_id"] == view_id
    assert result is None