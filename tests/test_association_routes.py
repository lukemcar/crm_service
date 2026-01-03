"""Tests for the Association admin and tenant routes.

These tests ensure that the refactored association endpoints delegate to the
service layer with the correct parameters and populate audit fields from
``X-User`` headers.  A ``DummySession`` type is used to avoid requiring
a real database connection.  Service functions are monkeypatched to
capture their inputs and return predictable results.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.association import AssociationCreate, AssociationRead
import app.domain.services.association_service as association_service

from app.api.routes.associations_admin_route import (
    list_associations_admin,
    create_association_admin,
    delete_association_admin,
)
from app.api.routes.associations_tenant_route import (
    list_associations_endpoint,
    create_association_endpoint,
    delete_association_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in for SQLAlchemy Session to satisfy type hints."""

    pass


def _fake_association_read(
    tenant_id: uuid.UUID,
    association_id: uuid.UUID,
    from_object_type: str = "contact",
    from_object_id: Optional[uuid.UUID] = None,
    to_object_type: str = "company",
    to_object_id: Optional[uuid.UUID] = None,
    association_type: Optional[str] = None,
    created_by: str = "tester",
) -> AssociationRead:
    now = datetime.now(timezone.utc)
    return AssociationRead(
        id=association_id,
        tenant_id=tenant_id,
        from_object_type=from_object_type,
        from_object_id=from_object_id or uuid.uuid4(),
        to_object_type=to_object_type,
        to_object_id=to_object_id or uuid.uuid4(),
        association_type=association_type,
        created_at=now,
        created_by=created_by,
    )


# ---------------------------------------------------------------------------
# Admin list
# ---------------------------------------------------------------------------


def test_list_associations_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_associations: List[AssociationRead] = [
        _fake_association_read(tenant_id=tenant_id, association_id=uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_associations, total

    monkeypatch.setattr(association_service, "service_list_associations", fake_list)

    result = list_associations_admin(
        tenant_id=tenant_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["limit"] is None
    assert captured["offset"] is None
    assert result.total == total
    assert len(result.items) == len(fake_associations)


# ---------------------------------------------------------------------------
# Admin create
# ---------------------------------------------------------------------------


def test_create_association_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AssociationCreate(
        from_object_type="contact",
        from_object_id=uuid.uuid4(),
        to_object_type="company",
        to_object_id=uuid.uuid4(),
    )
    fake_assoc = _fake_association_read(
        tenant_id=tenant_id,
        association_id=uuid.uuid4(),
        from_object_type=payload.from_object_type,
        from_object_id=payload.from_object_id,
        to_object_type=payload.to_object_type,
        to_object_id=payload.to_object_id,
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_assoc

    monkeypatch.setattr(association_service, "service_create_association", fake_create)

    result = create_association_admin(
        tenant_id=tenant_id,
        association_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["association_in"] == payload
    assert captured["created_user"] == "tester"
    assert result.id == fake_assoc.id


# ---------------------------------------------------------------------------
# Tenant list
# ---------------------------------------------------------------------------


def test_list_associations_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_associations: List[AssociationRead] = [
        _fake_association_read(tenant_id=tenant_id, association_id=uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_associations, total

    monkeypatch.setattr(association_service, "list_associations", fake_list)

    result = list_associations_endpoint(
        tenant_id=tenant_id,
        limit=10,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["limit"] == 10
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_associations)


# ---------------------------------------------------------------------------
# Tenant create
# ---------------------------------------------------------------------------


def test_create_association_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AssociationCreate(
        from_object_type="contact",
        from_object_id=uuid.uuid4(),
        to_object_type="company",
        to_object_id=uuid.uuid4(),
    )
    fake_assoc = _fake_association_read(
        tenant_id=tenant_id,
        association_id=uuid.uuid4(),
        from_object_type=payload.from_object_type,
        from_object_id=payload.from_object_id,
        to_object_type=payload.to_object_type,
        to_object_id=payload.to_object_id,
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_assoc

    monkeypatch.setattr(association_service, "create_association", fake_create)

    result = create_association_endpoint(
        tenant_id=tenant_id,
        association_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["association_in"] == payload
    assert captured["created_user"] == "tester"
    assert result.id == fake_assoc.id


# ---------------------------------------------------------------------------
# Delete endpoints
# ---------------------------------------------------------------------------


def test_delete_association_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    association_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(association_service, "service_delete_association", fake_delete)

    result = delete_association_admin(
        tenant_id=tenant_id,
        association_id=association_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["association_id"] == association_id
    assert result is None


def test_delete_association_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    association_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(association_service, "delete_association", fake_delete)

    result = delete_association_endpoint(
        tenant_id=tenant_id,
        association_id=association_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["association_id"] == association_id
    assert result is None