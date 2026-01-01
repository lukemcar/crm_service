from __future__ import annotations

import uuid
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.group_profile import (
    TenantCreateGroupProfile,
    GroupProfileUpdate,
    GroupProfileOut,
)
from app.domain.services import group_profile_service

from app.api.routes.group_profiles_tenant_route import (
    list_group_profiles_endpoint,
    create_group_profile_endpoint,
    update_group_profile_endpoint,
    get_group_profile_endpoint,
    delete_group_profile_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_group_profile_out(
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
    group_id: uuid.UUID,
    profile_type: str = "support_queue",
    is_support_queue: bool = True,
) -> GroupProfileOut:
    return GroupProfileOut(
        id=profile_id,
        tenant_id=tenant_id,
        group_id=group_id,
        profile_type=profile_type,
        is_support_queue=is_support_queue,
        is_assignable=True,
        default_sla_policy_id=None,
        routing_config=None,
        ai_work_mode_default="human_only",
        business_hours_id=None,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_group_profiles_endpoint
# ---------------------------------------------------------------------------


def test_list_group_profiles_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_profiles = [
        _fake_group_profile_out(
            tenant_id=tenant_id,
            profile_id=uuid.uuid4(),
            group_id=uuid.uuid4(),
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_profiles, total

    monkeypatch.setattr(group_profile_service, "list_group_profiles", fake_list)

    result = list_group_profiles_endpoint(
        tenant_id=tenant_id,
        profile_type="support_queue",
        is_support_queue=True,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["profile_type"] == "support_queue"
    assert captured_kwargs["is_support_queue"] is True
    assert result.total == total
    assert result.items == fake_profiles


# ---------------------------------------------------------------------------
# create_group_profile_endpoint
# ---------------------------------------------------------------------------


def test_create_group_profile_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    request = TenantCreateGroupProfile(group_id=uuid.uuid4())
    fake_profile = _fake_group_profile_out(
        tenant_id=tenant_id,
        profile_id=uuid.uuid4(),
        group_id=request.group_id,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_profile

    monkeypatch.setattr(group_profile_service, "create_group_profile", fake_create)

    result = create_group_profile_endpoint(
        tenant_id=tenant_id,
        profile_in=request,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == request
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_profile


# ---------------------------------------------------------------------------
# update_group_profile_endpoint
# ---------------------------------------------------------------------------


def test_update_group_profile_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = GroupProfileUpdate(profile_type="sales_team")
    fake_profile = _fake_group_profile_out(
        tenant_id=tenant_id,
        profile_id=profile_id,
        group_id=uuid.uuid4(),
        profile_type="sales_team",
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_profile

    monkeypatch.setattr(group_profile_service, "update_group_profile", fake_update)

    result = update_group_profile_endpoint(
        tenant_id=tenant_id,
        profile_id=profile_id,
        profile_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["profile_id"] == profile_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_profile


# ---------------------------------------------------------------------------
# get_group_profile_endpoint
# ---------------------------------------------------------------------------


def test_get_group_profile_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    fake_db = DummySession()
    fake_profile = _fake_group_profile_out(
        tenant_id=tenant_id,
        profile_id=profile_id,
        group_id=uuid.uuid4(),
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_profile

    monkeypatch.setattr(group_profile_service, "get_group_profile", fake_get)

    result = get_group_profile_endpoint(
        tenant_id=tenant_id,
        profile_id=profile_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["profile_id"] == profile_id
    assert result == fake_profile


# ---------------------------------------------------------------------------
# delete_group_profile_endpoint
# ---------------------------------------------------------------------------


def test_delete_group_profile_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    fake_db = DummySession()
    called = {"called": False}

    def fake_delete(db, **kwargs):
        called["called"] = True
        return None

    monkeypatch.setattr(group_profile_service, "delete_group_profile", fake_delete)

    result = delete_group_profile_endpoint(
        tenant_id=tenant_id,
        profile_id=profile_id,
        db=fake_db,
        x_user="tester",
    )

    assert called["called"] is True
    assert result is None