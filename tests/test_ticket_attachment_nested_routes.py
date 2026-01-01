from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_attachment import (
    TenantCreateTicketAttachment,
    TicketAttachmentOut,
)
from app.domain.services import ticket_attachment_service

from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_attachments_endpoint,
    create_ticket_attachment_endpoint,
    delete_ticket_attachment_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_attachment_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    attachment_id: uuid.UUID,
    file_name: str = "file.txt",
    content_type: Optional[str] = None,
    file_size_bytes: Optional[int] = None,
    storage_provider: Optional[str] = None,
    storage_key: str = "key",
    checksum_sha256: Optional[str] = None,
    ticket_message_id: Optional[uuid.UUID] = None,
) -> TicketAttachmentOut:
    return TicketAttachmentOut(
        id=attachment_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_message_id=ticket_message_id,
        file_name=file_name,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        storage_provider=storage_provider,
        storage_key=storage_key,
        checksum_sha256=checksum_sha256,
        created_at=None,
        created_by="tester",
    )


def test_list_ticket_attachments_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_attachments = [
        _fake_attachment_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            attachment_id=uuid.uuid4(),
            file_name="doc.pdf",
            storage_provider="s3",
            storage_key="doc.pdf",
            ticket_message_id=None,
        )
    ]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_attachments

    monkeypatch.setattr(ticket_attachment_service, "list_ticket_attachments", fake_list)

    result = list_ticket_attachments_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_message_id=None,
        storage_provider="s3",
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["ticket_message_id"] is None
    assert captured_kwargs["storage_provider"] == "s3"
    assert result == fake_attachments


def test_create_ticket_attachment_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketAttachment(
        file_name="image.png",
        content_type="image/png",
        file_size_bytes=1234,
        storage_provider="s3",
        storage_key="image.png",
        checksum_sha256=None,
        ticket_message_id=None,
    )
    fake_attachment = _fake_attachment_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        attachment_id=uuid.uuid4(),
        file_name=payload.file_name,
        content_type=payload.content_type,
        file_size_bytes=payload.file_size_bytes,
        storage_provider=payload.storage_provider,
        storage_key=payload.storage_key,
        checksum_sha256=payload.checksum_sha256,
        ticket_message_id=payload.ticket_message_id,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_attachment

    monkeypatch.setattr(ticket_attachment_service, "create_ticket_attachment", fake_create)

    result = create_ticket_attachment_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        attachment_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_attachment


def test_delete_ticket_attachment_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    attachment_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_attachment_service, "delete_ticket_attachment", fake_delete)

    result = delete_ticket_attachment_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        attachment_id=attachment_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["attachment_id"] == attachment_id
    assert result is None