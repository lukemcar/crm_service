"""
Tests for tenant‑scoped knowledge base category endpoints.

These tests ensure that the route handlers delegate correctly to the service layer,
propagate tenant identifiers, and use the `X‑User` header for audit fields when
creating or updating categories.  They follow the same pattern as existing tests
for other support domain endpoints.
"""

from __future__ import annotations

import uuid
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.kb_category import (
    TenantCreateKbCategory,
    KbCategoryUpdate,
    KbCategoryOut,
)
from app.domain.services import kb_category_service
from app.api.routes.kb_categories_tenant_route import (
    list_kb_categories_tenant_endpoint,
    create_kb_category_tenant_endpoint,
    update_kb_category_tenant_endpoint,
    get_kb_category_tenant_endpoint,
    delete_kb_category_tenant_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without requiring a real DB."""

    pass


def _fake_kb_category_out(
    tenant_id: uuid.UUID,
    category_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
    is_active: bool = True,
) -> KbCategoryOut:
    """Construct a fake KbCategoryOut for use in tests."""
    return KbCategoryOut(
        id=category_id,
        tenant_id=tenant_id,
        name=name,
        description=description,
        is_active=is_active,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_kb_categories_tenant_endpoint
# ---------------------------------------------------------------------------


def test_list_kb_categories_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_categories = [
        _fake_kb_category_out(
            tenant_id=tenant_id,
            category_id=uuid.uuid4(),
            name="Category 1",
        ),
        _fake_kb_category_out(
            tenant_id=tenant_id,
            category_id=uuid.uuid4(),
            name="Category 2",
            is_active=False,
        ),
    ]
    total = len(fake_categories)
    captured_kwargs: dict = {}

    def fake_list(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_categories, total

    monkeypatch.setattr(kb_category_service, "list_kb_categories", fake_list)

    result = list_kb_categories_tenant_endpoint(
        tenant_id=tenant_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    # Ensure the service was called with correct parameters
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert result == [c for c in fake_categories]


# ---------------------------------------------------------------------------
# create_kb_category_tenant_endpoint
# ---------------------------------------------------------------------------


def test_create_kb_category_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateKbCategory(name="New Category", description="Test", is_active=True)
    fake_category = _fake_kb_category_out(
        tenant_id=tenant_id,
        category_id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_create(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_category

    monkeypatch.setattr(kb_category_service, "create_kb_category", fake_create)

    result = create_kb_category_tenant_endpoint(
        tenant_id=tenant_id,
        category_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_category


# ---------------------------------------------------------------------------
# update_kb_category_tenant_endpoint
# ---------------------------------------------------------------------------


def test_update_kb_category_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    category_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = KbCategoryUpdate(name="Updated Name", description=None)
    fake_category = _fake_kb_category_out(
        tenant_id=tenant_id,
        category_id=category_id,
        name="Updated Name",
        description=None,
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_update(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_category

    monkeypatch.setattr(kb_category_service, "update_kb_category", fake_update)

    result = update_kb_category_tenant_endpoint(
        tenant_id=tenant_id,
        category_id=category_id,
        category_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["category_id"] == category_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_category


# ---------------------------------------------------------------------------
# get_kb_category_tenant_endpoint
# ---------------------------------------------------------------------------


def test_get_kb_category_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    category_id = uuid.uuid4()
    fake_db = DummySession()
    fake_category = _fake_kb_category_out(
        tenant_id=tenant_id,
        category_id=category_id,
        name="Category",
    )
    captured_kwargs: dict = {}

    def fake_get(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_category

    monkeypatch.setattr(kb_category_service, "get_kb_category", fake_get)

    result = get_kb_category_tenant_endpoint(
        tenant_id=tenant_id,
        category_id=category_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["category_id"] == category_id
    assert result == fake_category


# ---------------------------------------------------------------------------
# delete_kb_category_tenant_endpoint
# ---------------------------------------------------------------------------


def test_delete_kb_category_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    category_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        # delete returns None
        return None

    monkeypatch.setattr(kb_category_service, "delete_kb_category", fake_delete)

    result = delete_kb_category_tenant_endpoint(
        tenant_id=tenant_id,
        category_id=category_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["category_id"] == category_id
    assert captured_kwargs["deleted_by"] == "tester"
    assert result is None