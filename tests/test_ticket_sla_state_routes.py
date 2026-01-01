from __future__ import annotations

import uuid
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_sla_state import (
    TicketSlaStateUpdate,
    TicketSlaStateOut,
)
from app.domain.services import ticket_sla_state_service

from app.api.routes.ticket_sla_state_tenant_route import (
    get_ticket_sla_state_endpoint as tenant_get_sla_state,
)
from app.api.routes.ticket_sla_state_admin_route import (
    get_ticket_sla_state_admin as admin_get_sla_state,
    update_ticket_sla_state_admin as admin_update_sla_state,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""


def _fake_sla_state_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    state_id: uuid.UUID,
    sla_policy_id: Optional[uuid.UUID] = None,
) -> TicketSlaStateOut:
    return TicketSlaStateOut(
        id=state_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        sla_policy_id=sla_policy_id,
        first_response_due_at=None,
        next_response_due_at=None,
        resolution_due_at=None,
        first_response_breached=False,
        next_response_breached=False,
        resolution_breached=False,
        last_computed_at="2022-01-01T00:00:00Z",
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


def test_tenant_get_ticket_sla_state_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_state = _fake_sla_state_out(
        tenant_id=tenant_id, ticket_id=ticket_id, state_id=uuid.uuid4()
    )
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        # return list with one state and total 1
        return [fake_state], 1

    monkeypatch.setattr(ticket_sla_state_service, "list_ticket_sla_states", fake_list)

    result = tenant_get_sla_state(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_state


def test_admin_get_ticket_sla_state_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_state = _fake_sla_state_out(
        tenant_id=tenant_id, ticket_id=ticket_id, state_id=uuid.uuid4()
    )
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return [fake_state], 1

    monkeypatch.setattr(ticket_sla_state_service, "list_ticket_sla_states", fake_list)

    result = admin_get_sla_state(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_state


def test_admin_update_ticket_sla_state_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = TicketSlaStateUpdate(first_response_breached=True)
    fake_state = _fake_sla_state_out(
        tenant_id=tenant_id, ticket_id=ticket_id, state_id=uuid.uuid4()
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_state

    monkeypatch.setattr(ticket_sla_state_service, "update_ticket_sla_state", fake_update)

    result = admin_update_sla_state(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        state_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_state
