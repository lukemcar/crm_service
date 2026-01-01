from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.tenant_user_shadow import TenantUserShadowOut
from app.domain.schemas.tenant_group_shadow import TenantGroupShadowOut
from app.domain.services import tenant_user_shadow_service, tenant_group_shadow_service

# Route functions and router objects
from app.api.routes.tenant_users_shadow_tenant_route import (
    list_tenant_users_endpoint,
    get_tenant_user_endpoint,
    router as tenant_users_router,
)
from app.api.routes.tenant_groups_shadow_tenant_route import (
    list_tenant_groups_endpoint,
    get_tenant_group_endpoint,
    router as tenant_groups_router,
)


class DummySession(Session):
    """Lightweight stand‑in so type hints are happy without a real DB."""
    pass


def _fake_user_out(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str | None = None,
    email: str | None = None,
) -> TenantUserShadowOut:
    now = datetime.now(timezone.utc)
    return TenantUserShadowOut(
        tenant_id=tenant_id,
        user_id=user_id,
        display_name=name,
        email=email,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _fake_group_out(
    tenant_id: uuid.UUID,
    group_id: uuid.UUID,
    name: str,
) -> TenantGroupShadowOut:
    now = datetime.now(timezone.utc)
    return TenantGroupShadowOut(
        id=group_id,
        tenant_id=tenant_id,
        group_name=name,
        group_key=None,
        description=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Tenant user projection endpoints
# ---------------------------------------------------------------------------


def test_list_tenant_users_endpoint_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}
    # Patch the service to capture arguments and return an empty list
    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return [], 0
    monkeypatch.setattr(tenant_user_shadow_service, "list_tenant_users", fake_list)
    result = list_tenant_users_endpoint(
        tenant_id=tenant_id,
        display_name="john",
        email="example@example.com",
        limit=5,
        offset=0,
        db=fake_db,
    )
    # Verify service was called with correct parameters
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["display_name"] == "john"
    assert captured_kwargs["email"] == "example@example.com"
    assert captured_kwargs["limit"] == 5
    assert captured_kwargs["offset"] == 0
    # Verify returned pagination envelope
    assert result.items == []
    assert result.total == 0


def test_get_tenant_user_endpoint_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    fake_db = DummySession()
    fake_user = _fake_user_out(tenant_id, user_id, name="Jane Doe", email="jane@example.com")
    captured_kwargs: dict = {}
    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_user
    monkeypatch.setattr(tenant_user_shadow_service, "get_tenant_user", fake_get)
    result = get_tenant_user_endpoint(
        tenant_id=tenant_id,
        user_id=user_id,
        db=fake_db,
    )
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["user_id"] == user_id
    assert result == fake_user


def test_tenant_user_routes_are_read_only() -> None:
    """Ensure no POST/PATCH/DELETE routes exist on tenant user projections."""
    methods = set()
    for route in tenant_users_router.routes:
        # starlette routing stores methods per route endpoint
        if hasattr(route, "methods"):
            methods.update(route.methods)
    # Only GET and HEAD (implicitly added by FastAPI) should be present
    disallowed = {"POST", "PUT", "PATCH", "DELETE"}
    assert methods.isdisjoint(disallowed)


# ---------------------------------------------------------------------------
# Tenant group projection endpoints
# ---------------------------------------------------------------------------


def test_list_tenant_groups_endpoint_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}
    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return [], 0
    monkeypatch.setattr(tenant_group_shadow_service, "list_tenant_groups", fake_list)
    result = list_tenant_groups_endpoint(
        tenant_id=tenant_id,
        name="support",
        key="support-key",
        limit=3,
        offset=1,
        db=fake_db,
    )
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["name"] == "support"
    assert captured_kwargs["key"] == "support-key"
    assert captured_kwargs["limit"] == 3
    assert captured_kwargs["offset"] == 1
    assert result.items == []
    assert result.total == 0


def test_get_tenant_group_endpoint_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    group_id = uuid.uuid4()
    fake_db = DummySession()
    fake_group = _fake_group_out(tenant_id, group_id, name="Support Team")
    captured_kwargs: dict = {}
    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_group
    monkeypatch.setattr(tenant_group_shadow_service, "get_tenant_group", fake_get)
    result = get_tenant_group_endpoint(
        tenant_id=tenant_id,
        group_id=group_id,
        db=fake_db,
    )
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["group_id"] == group_id
    assert result == fake_group


def test_tenant_group_routes_are_read_only() -> None:
    methods = set()
    for route in tenant_groups_router.routes:
        if hasattr(route, "methods"):
            methods.update(route.methods)
    disallowed = {"POST", "PUT", "PATCH", "DELETE"}
    assert methods.isdisjoint(disallowed)
