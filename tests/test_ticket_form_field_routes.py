from __future__ import annotations

import uuid
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_form_field import (
    TenantCreateTicketFormField,
    TicketFormFieldUpdate,
    TicketFormFieldOut,
)
from app.domain.services import ticket_form_field_service

from app.api.routes.ticket_form_fields_tenant_route import (
    list_ticket_form_fields_endpoint,
    create_ticket_form_field_endpoint,
    update_ticket_form_field_endpoint,
    get_ticket_form_field_endpoint,
    delete_ticket_form_field_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_ticket_form_field_out(
    tenant_id: uuid.UUID,
    form_field_id: uuid.UUID,
    form_id: uuid.UUID,
    field_def_id: uuid.UUID,
    display_order: int,
) -> TicketFormFieldOut:
    return TicketFormFieldOut(
        id=form_field_id,
        tenant_id=tenant_id,
        ticket_form_id=form_id,
        ticket_field_def_id=field_def_id,
        display_order=display_order,
        created_at=None,
        created_by="tester",
    )


# ---------------------------------------------------------------------------
# list_ticket_form_fields_endpoint
# ---------------------------------------------------------------------------


def test_list_ticket_form_fields_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()
    fake_fields: List[TicketFormFieldOut] = [
        _fake_ticket_form_field_out(
            tenant_id=tenant_id,
            form_field_id=uuid.uuid4(),
            form_id=form_id,
            field_def_id=field_def_id,
            display_order=0,
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_fields, total

    monkeypatch.setattr(ticket_form_field_service, "list_ticket_form_fields", fake_list)

    result = list_ticket_form_fields_endpoint(
        tenant_id=tenant_id,
        ticket_form_id=form_id,
        ticket_field_def_id=field_def_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_form_id"] == form_id
    assert captured_kwargs["ticket_field_def_id"] == field_def_id
    assert result.total == total
    assert result.items == fake_fields


# ---------------------------------------------------------------------------
# create_ticket_form_field_endpoint
# ---------------------------------------------------------------------------


def test_create_ticket_form_field_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketFormField(
        ticket_form_id=uuid.uuid4(),
        ticket_field_def_id=uuid.uuid4(),
        display_order=1,
    )
    fake_field = _fake_ticket_form_field_out(
        tenant_id=tenant_id,
        form_field_id=uuid.uuid4(),
        form_id=payload.ticket_form_id,
        field_def_id=payload.ticket_field_def_id,
        display_order=payload.display_order,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_field

    monkeypatch.setattr(ticket_form_field_service, "create_ticket_form_field", fake_create)

    result = create_ticket_form_field_endpoint(
        tenant_id=tenant_id,
        form_field_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_field


# ---------------------------------------------------------------------------
# update_ticket_form_field_endpoint
# ---------------------------------------------------------------------------


def test_update_ticket_form_field_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_field_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = TicketFormFieldUpdate(display_order=2)
    fake_field = _fake_ticket_form_field_out(
        tenant_id=tenant_id,
        form_field_id=form_field_id,
        form_id=uuid.uuid4(),
        field_def_id=uuid.uuid4(),
        display_order=2,
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_field

    monkeypatch.setattr(ticket_form_field_service, "update_ticket_form_field", fake_update)

    result = update_ticket_form_field_endpoint(
        tenant_id=tenant_id,
        form_field_id=form_field_id,
        form_field_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_field_id"] == form_field_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_field


# ---------------------------------------------------------------------------
# get_ticket_form_field_endpoint
# ---------------------------------------------------------------------------


def test_get_ticket_form_field_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_field_id = uuid.uuid4()
    fake_db = DummySession()
    fake_field = _fake_ticket_form_field_out(
        tenant_id=tenant_id,
        form_field_id=form_field_id,
        form_id=uuid.uuid4(),
        field_def_id=uuid.uuid4(),
        display_order=0,
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_field

    monkeypatch.setattr(ticket_form_field_service, "get_ticket_form_field", fake_get)

    result = get_ticket_form_field_endpoint(
        tenant_id=tenant_id,
        form_field_id=form_field_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_field_id"] == form_field_id
    assert result == fake_field


# ---------------------------------------------------------------------------
# delete_ticket_form_field_endpoint
# ---------------------------------------------------------------------------


def test_delete_ticket_form_field_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_field_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_form_field_service, "delete_ticket_form_field", fake_delete)

    result = delete_ticket_form_field_endpoint(
        tenant_id=tenant_id,
        form_field_id=form_field_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_field_id"] == form_field_id
    # x_user is ignored for deletions
    assert result is None
