from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_message import (
    TenantCreateTicketMessage,
    TicketMessageOut,
)
from app.domain.services import ticket_message_service

from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_messages_endpoint,
    create_ticket_message_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_message_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    message_id: uuid.UUID,
    body: str,
    author_type: str = "agent",
    is_public: bool = True,
    channel_type: str = "internal",
    author_contact_id: Optional[uuid.UUID] = None,
    author_user_id: Optional[uuid.UUID] = None,
    author_display_name: Optional[str] = None,
    subject: Optional[str] = None,
    external_ref: Optional[str] = None,
    provider_metadata: Optional[Dict[str, Any]] = None,
) -> TicketMessageOut:
    """
    Build a ``TicketMessageOut`` instance for tests.

    The ``metadata`` field on the domain model was renamed to ``provider_metadata``
    to avoid conflicts with SQLAlchemy's reserved names.  Tests should use
    ``provider_metadata`` instead of ``metadata`` when constructing message
    objects.
    """
    return TicketMessageOut(
        id=message_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        author_type=author_type,
        author_contact_id=author_contact_id,
        author_user_id=author_user_id,
        author_display_name=author_display_name,
        is_public=is_public,
        channel_type=channel_type,
        external_ref=external_ref,
        subject=subject,
        body=body,
        provider_metadata=provider_metadata,
        created_at=None,
        created_by="tester",
    )


def test_list_ticket_messages_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_messages = [
        _fake_message_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            message_id=uuid.uuid4(),
            body="Hello",
            author_type="agent",
            is_public=True,
            channel_type="internal",
            author_user_id=uuid.uuid4(),
        )
    ]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_messages

    monkeypatch.setattr(ticket_message_service, "list_ticket_messages", fake_list)

    result = list_ticket_messages_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        author_type="agent",
        is_public=True,
        channel_type="internal",
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["author_type"] == "agent"
    assert captured_kwargs["is_public"] is True
    assert captured_kwargs["channel_type"] == "internal"
    assert result == fake_messages


def test_create_ticket_message_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketMessage(
        author_type="agent",
        author_contact_id=None,
        author_user_id=uuid.uuid4(),
        author_display_name=None,
        is_public=True,
        channel_type="internal",
        external_ref=None,
        subject=None,
        body="Hello",
        # renamed from metadata to provider_metadata in the schema
        provider_metadata=None,
    )
    fake_message = _fake_message_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        message_id=uuid.uuid4(),
        body=payload.body,
        author_type=payload.author_type,
        is_public=payload.is_public,
        channel_type=payload.channel_type,
        author_user_id=payload.author_user_id,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_message

    monkeypatch.setattr(ticket_message_service, "create_ticket_message", fake_create)

    result = create_ticket_message_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        message_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_message