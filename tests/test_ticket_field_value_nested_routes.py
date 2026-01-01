from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_field_value import (
    TenantCreateTicketFieldValue,
    TicketFieldValueUpdate,
    TicketFieldValueOut,
)
from app.domain.services import ticket_field_value_service

from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_field_values_endpoint,
    create_ticket_field_value_endpoint,
    get_ticket_field_value_endpoint,
    update_ticket_field_value_endpoint,
    delete_ticket_field_value_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_field_value_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    value_id: uuid.UUID,
    field_def_id: uuid.UUID,
    value_text: Optional[str] = None,
    value_number: Optional[float] = None,
    value_bool: Optional[bool] = None,
    value_date: Optional[str] = None,
    value_ts: Optional[str] = None,
    value_json: Optional[dict] = None,
) -> TicketFieldValueOut:
    return TicketFieldValueOut(
        id=value_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_field_def_id=field_def_id,
        value_text=value_text,
        value_number=value_number,
        value_bool=value_bool,
        value_date=value_date,
        value_ts=value_ts,
        value_json=value_json,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


def test_list_ticket_field_values_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()
    fake_values: List[TicketFieldValueOut] = [
        _fake_field_value_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            value_id=uuid.uuid4(),
            field_def_id=field_def_id,
            value_text="abc",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_values, total

    monkeypatch.setattr(
        ticket_field_value_service, "list_ticket_field_values", fake_list
    )

    result = list_ticket_field_values_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_field_def_id=field_def_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["ticket_field_def_id"] == field_def_id
    assert result == fake_values


def test_create_ticket_field_value_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketFieldValue(
        ticket_field_def_id=uuid.uuid4(),
        value_text="hello",
    )
    fake_value = _fake_field_value_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=uuid.uuid4(),
        field_def_id=payload.ticket_field_def_id,
        value_text=payload.value_text,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_value

    monkeypatch.setattr(
        ticket_field_value_service, "create_ticket_field_value", fake_create
    )

    result = create_ticket_field_value_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_value


def test_get_ticket_field_value_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    value_id = uuid.uuid4()
    fake_db = DummySession()
    fake_value = _fake_field_value_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
        field_def_id=uuid.uuid4(),
        value_text="val",
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_value

    monkeypatch.setattr(
        ticket_field_value_service, "get_ticket_field_value", fake_get
    )

    result = get_ticket_field_value_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["value_id"] == value_id
    assert result == fake_value


def test_update_ticket_field_value_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    value_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = TicketFieldValueUpdate(value_text="updated")
    fake_value = _fake_field_value_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
        field_def_id=uuid.uuid4(),
        value_text="updated",
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_value

    monkeypatch.setattr(
        ticket_field_value_service, "update_ticket_field_value", fake_update
    )

    result = update_ticket_field_value_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
        value_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["value_id"] == value_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_value


def test_delete_ticket_field_value_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    value_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(
        ticket_field_value_service, "delete_ticket_field_value", fake_delete
    )

    result = delete_ticket_field_value_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["value_id"] == value_id
    assert result is None
