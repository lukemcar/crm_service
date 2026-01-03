"""Tests for the List Membership admin and tenant routes.

These tests validate that the new list membership endpoints call the
appropriate service functions with the correct parameters and handle
auditing via the ``X‑User`` header.  The tests also ensure that
tenant and list identifiers are propagated correctly through nested
paths.  A lightweight ``DummySession`` class is used in place of a
real SQLAlchemy session to satisfy type hints.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.list_membership import ListMembershipCreate, ListMembershipRead
import app.domain.services.list_membership_service as membership_service
import app.domain.services.list_service as list_service

from app.api.routes.list_memberships_admin_route import (
    list_memberships as list_memberships_admin,
    create_membership as create_membership_admin,
    delete_membership as delete_membership_admin,
)
from app.api.routes.list_memberships_tenant_route import (
    list_memberships as list_memberships_tenant,
    create_membership as create_membership_tenant,
    get_membership as get_membership_tenant,
    delete_membership as delete_membership_tenant,
)


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    pass


def _fake_membership_read(
    list_id: uuid.UUID,
    membership_id: uuid.UUID,
    member_id: uuid.UUID,
    member_type: str = "contact",
    created_by: str = "tester",
) -> ListMembershipRead:
    """Construct a ``ListMembershipRead`` with sensible defaults."""
    now = datetime.now(timezone.utc)
    return ListMembershipRead(
        id=membership_id,
        list_id=list_id,
        member_id=member_id,
        member_type=member_type,
        created_at=now,
        created_by=created_by,
    )


def test_list_memberships_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should pass list ID, tenant ID and pagination to the service."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    fake_memberships: List[ListMembershipRead] = [
        _fake_membership_read(list_id, uuid.uuid4(), uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    # Stub list_service.get_list to return a truthy value when tenant_id is provided
    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_memberships, total

    monkeypatch.setattr(membership_service, "service_list_memberships", fake_list)

    result = list_memberships_admin(
        list_id=list_id,
        tenant_id=tenant_id,
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_memberships)


def test_create_membership_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should validate list ownership and forward audit info."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ListMembershipCreate(
        list_id=list_id,
        member_id=uuid.uuid4(),
        member_type="contact",
    )
    fake_membership = _fake_membership_read(
        list_id=list_id,
        membership_id=uuid.uuid4(),
        member_id=payload.member_id,
        member_type=payload.member_type,
    )
    captured: dict = {}

    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_membership

    monkeypatch.setattr(membership_service, "service_create_membership", fake_create)

    result = create_membership_admin(
        list_id=list_id,
        tenant_id=tenant_id,
        membership_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert captured["membership_in"] == payload
    assert captured["created_user"] == "creator"
    assert result.id == fake_membership.id


def test_delete_membership_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should validate membership and list ownership."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    # Stub service_get_membership to return an object with list_id and tenant_id
    class DummyMembership:
        def __init__(self, mid: uuid.UUID, lid: uuid.UUID, tid: uuid.UUID):
            self.id = mid
            self.list_id = lid
            self.tenant_id = tid

    monkeypatch.setattr(
        membership_service,
        "service_get_membership",
        lambda db, membership_id: DummyMembership(membership_id, list_id, tenant_id),
    )
    # Stub list_service.get_list to return a truthy value when tenant_id is provided
    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(membership_service, "service_delete_membership", fake_delete)

    result = delete_membership_admin(
        membership_id=membership_id,
        tenant_id=tenant_id,
        x_user="deleter",
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["membership_id"] == membership_id
    assert captured["deleted_user"] == "deleter"
    assert result.status_code == 204


def test_list_memberships_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant list endpoint should validate list ownership and forward pagination."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    fake_memberships: List[ListMembershipRead] = [
        _fake_membership_read(list_id, uuid.uuid4(), uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_memberships, total

    monkeypatch.setattr(membership_service, "service_list_memberships", fake_list)

    result = list_memberships_tenant(
        tenant_id=tenant_id,
        list_id=list_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert captured["limit"] is None
    assert captured["offset"] is None
    assert result.total == total
    assert len(result.items) == len(fake_memberships)


def test_create_membership_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant create endpoint should validate list ownership and forward audit info."""
    tenant_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    payload = ListMembershipCreate(
        list_id=list_id,
        member_id=uuid.uuid4(),
        member_type="contact",
    )
    fake_membership = _fake_membership_read(
        list_id=list_id,
        membership_id=uuid.uuid4(),
        member_id=payload.member_id,
        member_type=payload.member_type,
    )
    captured: dict = {}

    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_membership

    monkeypatch.setattr(membership_service, "service_create_membership", fake_create)

    result = create_membership_tenant(
        tenant_id=tenant_id,
        list_id=list_id,
        membership_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["list_id"] == list_id
    assert captured["membership_in"] == payload
    assert captured["created_user"] == "creator"
    assert result.id == fake_membership.id


def test_get_membership_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant get endpoint should validate membership and list ownership."""
    tenant_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()

    class DummyMembership:
        def __init__(self, mid: uuid.UUID, lid: uuid.UUID, tid: uuid.UUID):
            self.id = mid
            self.list_id = lid
            self.tenant_id = tid

    dummy_membership = DummyMembership(membership_id, list_id, tenant_id)

    monkeypatch.setattr(
        membership_service,
        "service_get_membership",
        lambda db, membership_id: dummy_membership,
    )
    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    result = get_membership_tenant(
        tenant_id=tenant_id,
        membership_id=membership_id,
        db=fake_db,
    )

    assert result.id == dummy_membership.id


def test_delete_membership_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant delete endpoint should validate membership and list ownership."""
    tenant_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    list_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    class DummyMembership:
        def __init__(self, mid: uuid.UUID, lid: uuid.UUID, tid: uuid.UUID):
            self.id = mid
            self.list_id = lid
            self.tenant_id = tid

    dummy_membership = DummyMembership(membership_id, list_id, tenant_id)

    monkeypatch.setattr(
        membership_service,
        "service_get_membership",
        lambda db, membership_id: dummy_membership,
    )
    monkeypatch.setattr(list_service, "get_list", lambda db, lid, tid: object())

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(membership_service, "service_delete_membership", fake_delete)

    result = delete_membership_tenant(
        tenant_id=tenant_id,
        membership_id=membership_id,
        db=fake_db,
        x_user="deleter",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["membership_id"] == membership_id
    assert captured["deleted_user"] == "deleter"
    assert result.status_code == 204