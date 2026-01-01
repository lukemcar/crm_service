from __future__ import annotations

import uuid
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_field_def import (
    TenantCreateTicketFieldDef,
    TicketFieldDefUpdate,
    TicketFieldDefOut,
)
from app.domain.services import ticket_field_def_service

from app.api.routes.ticket_field_defs_tenant_route import (
    list_ticket_field_defs_endpoint,
    create_ticket_field_def_endpoint,
    update_ticket_field_def_endpoint,
    get_ticket_field_def_endpoint,
    delete_ticket_field_def_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_ticket_field_def_out(
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
    field_key: str,
    label: str,
    field_type: str,
    is_required: bool = False,
    is_active: bool = True,
) -> TicketFieldDefOut:
    return TicketFieldDefOut(
        id=field_def_id,
        tenant_id=tenant_id,
        field_key=field_key,
        label=label,
        field_type=field_type,
        is_required=is_required,
        is_active=is_active,
        validation=None,
        ui_config=None,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_ticket_field_defs_endpoint
# ---------------------------------------------------------------------------


def test_list_ticket_field_defs_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_defs = [
        _fake_ticket_field_def_out(
            tenant_id=tenant_id,
            field_def_id=uuid.uuid4(),
            field_key="priority",
            label="Priority",
            field_type="select",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_defs, total

    monkeypatch.setattr(ticket_field_def_service, "list_ticket_field_defs", fake_list)

    result = list_ticket_field_defs_endpoint(
        tenant_id=tenant_id,
        field_type="select",
        is_active=True,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_type"] == "select"
    assert captured_kwargs["is_active"] is True
    assert result.total == total
    assert result.items == fake_defs


# ---------------------------------------------------------------------------
# create_ticket_field_def_endpoint
# ---------------------------------------------------------------------------


def test_create_ticket_field_def_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketFieldDef(
        field_key="priority",
        label="Priority",
        field_type="select",
        is_required=False,
        is_active=True,
        validation=None,
        ui_config=None,
    )
    fake_def = _fake_ticket_field_def_out(
        tenant_id=tenant_id,
        field_def_id=uuid.uuid4(),
        field_key=payload.field_key,
        label=payload.label,
        field_type=payload.field_type,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_def

    monkeypatch.setattr(ticket_field_def_service, "create_ticket_field_def", fake_create)

    result = create_ticket_field_def_endpoint(
        tenant_id=tenant_id,
        field_def_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_def


# ---------------------------------------------------------------------------
# update_ticket_field_def_endpoint
# ---------------------------------------------------------------------------


def test_update_ticket_field_def_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = TicketFieldDefUpdate(label="Urgency", field_type="select")
    fake_def = _fake_ticket_field_def_out(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        field_key="priority",
        label="Urgency",
        field_type="select",
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_def

    monkeypatch.setattr(ticket_field_def_service, "update_ticket_field_def", fake_update)

    result = update_ticket_field_def_endpoint(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        field_def_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_def_id"] == field_def_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_def


# ---------------------------------------------------------------------------
# get_ticket_field_def_endpoint
# ---------------------------------------------------------------------------


def test_get_ticket_field_def_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()
    fake_def = _fake_ticket_field_def_out(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        field_key="priority",
        label="Priority",
        field_type="select",
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_def

    monkeypatch.setattr(ticket_field_def_service, "get_ticket_field_def", fake_get)

    result = get_ticket_field_def_endpoint(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_def_id"] == field_def_id
    assert result == fake_def


# ---------------------------------------------------------------------------
# delete_ticket_field_def_endpoint
# ---------------------------------------------------------------------------


def test_delete_ticket_field_def_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_field_def_service, "delete_ticket_field_def", fake_delete)

    result = delete_ticket_field_def_endpoint(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_def_id"] == field_def_id
    assert result is None