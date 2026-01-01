from __future__ import annotations

import uuid
from typing import Optional, Dict, Any, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.support_macro import (
    TenantCreateSupportMacro,
    SupportMacroUpdate,
    SupportMacroOut,
)
from app.domain.services import support_macro_service

from app.api.routes.support_macros_tenant_route import (
    list_support_macros_endpoint,
    create_support_macro_endpoint,
    update_support_macro_endpoint,
    get_support_macro_endpoint,
    delete_support_macro_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""

    pass


def _fake_support_macro_out(
    tenant_id: uuid.UUID,
    macro_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
    is_active: bool = True,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> SupportMacroOut:
    return SupportMacroOut(
        id=macro_id,
        tenant_id=tenant_id,
        name=name,
        description=description,
        is_active=is_active,
        actions=actions or [
            {"operation": "set_status", "value": "open"}
        ],
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_support_macros_endpoint
# ---------------------------------------------------------------------------


def test_list_support_macros_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_macros = [
        _fake_support_macro_out(
            tenant_id=tenant_id,
            macro_id=uuid.uuid4(),
            name="Quick Reply",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_macros, total

    monkeypatch.setattr(support_macro_service, "list_support_macros", fake_list)

    result = list_support_macros_endpoint(
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
    assert result.items == fake_macros


# ---------------------------------------------------------------------------
# create_support_macro_endpoint
# ---------------------------------------------------------------------------


def test_create_support_macro_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateSupportMacro(
        name="Auto Assign",
        description="Assign ticket to Tier 2",
        is_active=True,
        actions=[{"operation": "assign_to_group", "value": "tier2"}],
    )
    fake_macro = _fake_support_macro_out(
        tenant_id=tenant_id,
        macro_id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        is_active=True,
        actions=payload.actions,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_macro

    monkeypatch.setattr(support_macro_service, "create_support_macro", fake_create)

    result = create_support_macro_endpoint(
        tenant_id=tenant_id,
        macro_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_macro


# ---------------------------------------------------------------------------
# update_support_macro_endpoint
# ---------------------------------------------------------------------------


def test_update_support_macro_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    macro_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = SupportMacroUpdate(name="Updated Macro", description="Updated desc")
    fake_macro = _fake_support_macro_out(
        tenant_id=tenant_id,
        macro_id=macro_id,
        name="Updated Macro",
        description="Updated desc",
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_macro

    monkeypatch.setattr(support_macro_service, "update_support_macro", fake_update)

    result = update_support_macro_endpoint(
        tenant_id=tenant_id,
        macro_id=macro_id,
        macro_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["macro_id"] == macro_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_macro


# ---------------------------------------------------------------------------
# get_support_macro_endpoint
# ---------------------------------------------------------------------------


def test_get_support_macro_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    macro_id = uuid.uuid4()
    fake_db = DummySession()
    fake_macro = _fake_support_macro_out(
        tenant_id=tenant_id,
        macro_id=macro_id,
        name="My Macro",
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_macro

    monkeypatch.setattr(support_macro_service, "get_support_macro", fake_get)

    result = get_support_macro_endpoint(
        tenant_id=tenant_id,
        macro_id=macro_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["macro_id"] == macro_id
    assert result == fake_macro


# ---------------------------------------------------------------------------
# delete_support_macro_endpoint
# ---------------------------------------------------------------------------


def test_delete_support_macro_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    macro_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(support_macro_service, "delete_support_macro", fake_delete)

    result = delete_support_macro_endpoint(
        tenant_id=tenant_id,
        macro_id=macro_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["macro_id"] == macro_id
    assert result is None