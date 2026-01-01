from __future__ import annotations

import uuid
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_form import (
    TenantCreateTicketForm,
    TicketFormUpdate,
    TicketFormOut,
)
from app.domain.services import ticket_form_service

from app.api.routes.ticket_forms_tenant_route import (
    list_ticket_forms_endpoint,
    create_ticket_form_endpoint,
    update_ticket_form_endpoint,
    get_ticket_form_endpoint,
    delete_ticket_form_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_ticket_form_out(
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
    is_active: bool = True,
) -> TicketFormOut:
    return TicketFormOut(
        id=form_id,
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
# list_ticket_forms_endpoint
# ---------------------------------------------------------------------------


def test_list_ticket_forms_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_forms = [
        _fake_ticket_form_out(
            tenant_id=tenant_id,
            form_id=uuid.uuid4(),
            name="Customer Feedback",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_forms, total

    monkeypatch.setattr(ticket_form_service, "list_ticket_forms", fake_list)

    result = list_ticket_forms_endpoint(
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
    assert result.items == fake_forms


# ---------------------------------------------------------------------------
# create_ticket_form_endpoint
# ---------------------------------------------------------------------------


def test_create_ticket_form_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketForm(name="NPS Survey", description="Net Promoter Score survey", is_active=True)
    fake_form = _fake_ticket_form_out(
        tenant_id=tenant_id,
        form_id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_form

    monkeypatch.setattr(ticket_form_service, "create_ticket_form", fake_create)

    result = create_ticket_form_endpoint(
        tenant_id=tenant_id,
        form_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_form


# ---------------------------------------------------------------------------
# update_ticket_form_endpoint
# ---------------------------------------------------------------------------


def test_update_ticket_form_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = TicketFormUpdate(name="Updated Name", description="Updated description")
    fake_form = _fake_ticket_form_out(
        tenant_id=tenant_id,
        form_id=form_id,
        name="Updated Name",
        description="Updated description",
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_form

    monkeypatch.setattr(ticket_form_service, "update_ticket_form", fake_update)

    result = update_ticket_form_endpoint(
        tenant_id=tenant_id,
        form_id=form_id,
        form_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_id"] == form_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_form


# ---------------------------------------------------------------------------
# get_ticket_form_endpoint
# ---------------------------------------------------------------------------


def test_get_ticket_form_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()
    fake_form = _fake_ticket_form_out(
        tenant_id=tenant_id,
        form_id=form_id,
        name="Support Form",
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_form

    monkeypatch.setattr(ticket_form_service, "get_ticket_form", fake_get)

    result = get_ticket_form_endpoint(
        tenant_id=tenant_id,
        form_id=form_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_id"] == form_id
    assert result == fake_form


# ---------------------------------------------------------------------------
# delete_ticket_form_endpoint
# ---------------------------------------------------------------------------


def test_delete_ticket_form_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_form_service, "delete_ticket_form", fake_delete)

    result = delete_ticket_form_endpoint(
        tenant_id=tenant_id,
        form_id=form_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_id"] == form_id
    # delete does not use x_user currently; ensure no extra keys
    assert result is None