from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket import (
    TenantCreateTicket,
    TicketUpdate,
    TicketOut,
)
from app.domain.services import ticket_service

from app.api.routes.tickets_tenant_route import (
    list_tickets_endpoint,
    create_ticket_endpoint,
    update_ticket_endpoint,
    get_ticket_endpoint,
    delete_ticket_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_ticket_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    subject: str,
    status: str = "new",
    priority: str = "normal",
    ticket_type: str = "question",
    assigned_group_id: Optional[uuid.UUID] = None,
    assigned_user_id: Optional[uuid.UUID] = None,
) -> TicketOut:
    """Construct a TicketOut object with minimal required fields for testing."""
    return TicketOut(
        id=ticket_id,
        tenant_id=tenant_id,
        requester_contact_id=None,
        company_id=None,
        inbound_channel_id=None,
        ticket_form_id=None,
        subject=subject,
        description=None,
        status=status,
        priority=priority,
        ticket_type=ticket_type,
        assigned_group_id=assigned_group_id,
        assigned_user_id=assigned_user_id,
        first_response_at=None,
        last_message_at=None,
        solved_at=None,
        closed_at=None,
        custom_fields=None,
        orchestration_workflow_key=None,
        orchestration_instance_id=None,
        orchestration_state=None,
        work_mode="human_only",
        ai_status="idle",
        ai_last_session_id=None,
        ai_last_agent_key=None,
        ai_last_outcome=None,
        ai_last_confidence=None,
        ai_last_completed_at=None,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_tickets_endpoint
# ---------------------------------------------------------------------------


def test_list_tickets_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_ticket = _fake_ticket_out(
        tenant_id=tenant_id,
        ticket_id=uuid.uuid4(),
        subject="Subject",
    )
    fake_list: List[TicketOut] = [fake_ticket]
    total = 1
    captured_kwargs: dict = {}

    def fake_list_tickets(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_list, total

    monkeypatch.setattr(ticket_service, "list_tickets", fake_list_tickets)

    result = list_tickets_endpoint(
        tenant_id=tenant_id,
        status="new",
        priority="normal",
        assigned_user_id=None,
        assigned_group_id=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["status"] == "new"
    assert captured_kwargs["priority"] == "normal"
    assert captured_kwargs["assigned_user_id"] is None
    assert captured_kwargs["assigned_group_id"] is None
    assert result.total == total
    assert result.items == fake_list


# ---------------------------------------------------------------------------
# create_ticket_endpoint
# ---------------------------------------------------------------------------


def test_create_ticket_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicket(
        subject="Subject",
        description=None,
        status="new",
        priority="normal",
        ticket_type="question",
        assigned_group_id=None,
        assigned_user_id=None,
        inbound_channel_id=None,
        ticket_form_id=None,
        custom_fields=None,
        work_mode="human_only",
        requester_contact_id=None,
        company_id=None,
    )
    fake_ticket = _fake_ticket_out(
        tenant_id=tenant_id,
        ticket_id=uuid.uuid4(),
        subject=payload.subject,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_ticket

    monkeypatch.setattr(ticket_service, "create_ticket", fake_create)

    result = create_ticket_endpoint(
        tenant_id=tenant_id,
        ticket_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_ticket


# ---------------------------------------------------------------------------
# update_ticket_endpoint
# ---------------------------------------------------------------------------


def test_update_ticket_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = TicketUpdate(subject="New Subject")
    fake_ticket = _fake_ticket_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        subject="New Subject",
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_ticket

    monkeypatch.setattr(ticket_service, "update_ticket", fake_update)

    result = update_ticket_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_ticket


# ---------------------------------------------------------------------------
# get_ticket_endpoint
# ---------------------------------------------------------------------------


def test_get_ticket_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_ticket = _fake_ticket_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        subject="Subject",
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_ticket

    monkeypatch.setattr(ticket_service, "get_ticket", fake_get)

    result = get_ticket_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_ticket


# ---------------------------------------------------------------------------
# delete_ticket_endpoint
# ---------------------------------------------------------------------------


def test_delete_ticket_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_service, "delete_ticket", fake_delete)

    result = delete_ticket_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    # delete_ticket_endpoint returns None on success
    assert result is None