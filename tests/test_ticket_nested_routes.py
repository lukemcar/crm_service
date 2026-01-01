from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_participant import (
    TenantCreateTicketParticipant,
    TicketParticipantOut,
)
from app.domain.schemas.ticket_tag import (
    TenantCreateTicketTag,
    TicketTagOut,
)
from app.domain.services import ticket_participant_service, ticket_tag_service

from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_participants_endpoint,
    create_ticket_participant_endpoint,
    delete_ticket_participant_endpoint,
    list_ticket_tags_endpoint,
    create_ticket_tag_endpoint,
    delete_ticket_tag_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_participant_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    participant_id: uuid.UUID,
    participant_type: str = "agent",
    role: str = "cc",
    contact_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
) -> TicketParticipantOut:
    return TicketParticipantOut(
        id=participant_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_type=participant_type,
        contact_id=contact_id,
        user_id=user_id,
        role=role,
        created_at=None,
        created_by="tester",
    )


def _fake_tag_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    tag_id: uuid.UUID,
    tag: str,
) -> TicketTagOut:
    return TicketTagOut(
        id=tag_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        tag=tag,
        created_at=None,
        created_by="tester",
    )


# ---------------------------------------------------------------------------
# Participant endpoints
# ---------------------------------------------------------------------------


def test_list_ticket_participants_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_participants = [
        _fake_participant_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            participant_id=uuid.uuid4(),
            participant_type="agent",
            role="cc",
            user_id=uuid.uuid4(),
        )
    ]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_participants

    monkeypatch.setattr(ticket_participant_service, "list_ticket_participants", fake_list)

    result = list_ticket_participants_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_type="agent",
        role="cc",
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["participant_type"] == "agent"
    assert captured_kwargs["role"] == "cc"
    assert result == fake_participants


def test_create_ticket_participant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketParticipant(
        participant_type="agent",
        role="cc",
        user_id=uuid.uuid4(),
        contact_id=None,
    )
    fake_participant = _fake_participant_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_id=uuid.uuid4(),
        participant_type="agent",
        role="cc",
        user_id=payload.user_id,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_participant

    monkeypatch.setattr(ticket_participant_service, "create_ticket_participant", fake_create)

    result = create_ticket_participant_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_participant


def test_delete_ticket_participant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_participant_service, "delete_ticket_participant", fake_delete)

    result = delete_ticket_participant_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_id=participant_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["participant_id"] == participant_id
    assert result is None


# ---------------------------------------------------------------------------
# Tag endpoints
# ---------------------------------------------------------------------------


def test_list_ticket_tags_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_tags = [
        _fake_tag_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            tag_id=uuid.uuid4(),
            tag="urgent",
        )
    ]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_tags

    monkeypatch.setattr(ticket_tag_service, "list_ticket_tags", fake_list)

    result = list_ticket_tags_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_tags


def test_create_ticket_tag_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketTag(tag="urgent")
    fake_tag = _fake_tag_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        tag_id=uuid.uuid4(),
        tag=payload.tag,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_tag

    monkeypatch.setattr(ticket_tag_service, "create_ticket_tag", fake_create)

    result = create_ticket_tag_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        tag_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_tag


def test_delete_ticket_tag_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    tag_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_tag_service, "delete_ticket_tag", fake_delete)

    result = delete_ticket_tag_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        tag_id=tag_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["tag_id"] == tag_id
    assert result is None