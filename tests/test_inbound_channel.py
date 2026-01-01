from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.inbound_channel import (
    TenantCreateInboundChannel,
    InboundChannelUpdate,
    InboundChannelOut,
)
from app.domain.services import inbound_channel_service

from app.api.routes.inbound_channels_tenant_route import (
    create_inbound_channel_endpoint,
    update_inbound_channel_endpoint,
    get_inbound_channel_endpoint,
    delete_inbound_channel_endpoint,
    list_inbound_channels_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_inbound_channel_out(
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
    channel_type: str,
    name: str,
    external_ref: Optional[str] = None,
    is_active: bool = True,
) -> InboundChannelOut:
    return InboundChannelOut(
        id=channel_id,
        tenant_id=tenant_id,
        channel_type=channel_type,
        name=name,
        external_ref=external_ref,
        config=None,
        is_active=is_active,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_inbound_channels_endpoint
# ---------------------------------------------------------------------------


def test_list_inbound_channels_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    fake_channels = [
        _fake_inbound_channel_out(
            tenant_id=tenant_id,
            channel_id=uuid.uuid4(),
            channel_type="email",
            name="Support Inbox",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_channels, total

    monkeypatch.setattr(inbound_channel_service, "list_inbound_channels", fake_list)

    result = list_inbound_channels_endpoint(
        tenant_id=tenant_id,
        channel_type="email",
        is_active=True,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["channel_type"] == "email"
    assert captured_kwargs["is_active"] is True
    assert result.total == total
    assert result.items == fake_channels


# ---------------------------------------------------------------------------
# create_inbound_channel_endpoint
# ---------------------------------------------------------------------------


def test_create_inbound_channel_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateInboundChannel(
        channel_type="email", name="Support", external_ref=None, config=None, is_active=True
    )

    fake_channel = _fake_inbound_channel_out(
        tenant_id=tenant_id,
        channel_id=uuid.uuid4(),
        channel_type=payload.channel_type,
        name=payload.name,
    )

    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_channel

    monkeypatch.setattr(inbound_channel_service, "create_inbound_channel", fake_create)

    result = create_inbound_channel_endpoint(
        tenant_id=tenant_id,
        channel_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_channel


# ---------------------------------------------------------------------------
# update_inbound_channel_endpoint
# ---------------------------------------------------------------------------


def test_update_inbound_channel_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = InboundChannelUpdate(name="New Name")

    fake_channel = _fake_inbound_channel_out(
        tenant_id=tenant_id,
        channel_id=channel_id,
        channel_type="email",
        name="New Name",
    )

    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_channel

    monkeypatch.setattr(inbound_channel_service, "update_inbound_channel", fake_update)

    result = update_inbound_channel_endpoint(
        tenant_id=tenant_id,
        channel_id=channel_id,
        channel_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["channel_id"] == channel_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_channel


# ---------------------------------------------------------------------------
# get_inbound_channel_endpoint
# ---------------------------------------------------------------------------


def test_get_inbound_channel_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    fake_db = DummySession()

    fake_channel = _fake_inbound_channel_out(
        tenant_id=tenant_id,
        channel_id=channel_id,
        channel_type="email",
        name="Support",
    )

    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_channel

    monkeypatch.setattr(inbound_channel_service, "get_inbound_channel", fake_get)

    result = get_inbound_channel_endpoint(
        tenant_id=tenant_id,
        channel_id=channel_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["channel_id"] == channel_id
    assert result == fake_channel


# ---------------------------------------------------------------------------
# delete_inbound_channel_endpoint
# ---------------------------------------------------------------------------


def test_delete_inbound_channel_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    fake_db = DummySession()

    captured: dict = {"called": False}

    def fake_delete(db, **kwargs):
        captured["called"] = True
        return None

    monkeypatch.setattr(inbound_channel_service, "delete_inbound_channel", fake_delete)

    result = delete_inbound_channel_endpoint(
        tenant_id=tenant_id,
        channel_id=channel_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured["called"] is True
    assert result is None