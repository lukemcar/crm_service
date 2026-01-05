from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.contact import TenantCreateContact, ContactOut
from app.domain.schemas.json_patch import JsonPatchRequest, JsonPatchOperation
from app.domain.services import contact_service

from app.api.routes.contacts_tenant_route import (
    create_contact_endpoint,
    get_contact_endpoint,
    patch_contact_endpoint,
    delete_contact_endpoint,
)


class DummySession(Session):
    """Lightweight stand-in so type hints are happy without a real DB."""
    pass


def _fake_contact_out(
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    first_name: str,
    last_name: str,
    created_by: str = "tester",
    updated_by: str = "tester",
    owned_by_user_id: uuid.UUID | None = None,
    owned_by_group_id: uuid.UUID | None = None,
) -> ContactOut:
    now = datetime.now(timezone.utc)

    # Most CRM schemas include nested collections; keep them empty by default.
    # If your ContactOut requires different names, adjust only these fields.
    return ContactOut(
        id=contact_id,
        tenant_id=tenant_id,
        first_name=first_name,
        middle_name=None,
        last_name=last_name,
        maiden_name=None,
        prefix=None,
        suffix=None,
        owned_by_user_id=owned_by_user_id,
        owned_by_group_id=owned_by_group_id,
        phones=[],
        emails=[],
        addresses=[],
        social_profiles=[],
        notes=[],
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


# ---------------------------------------------------------------------------
# create_contact_endpoint
# ---------------------------------------------------------------------------

def test_create_contact_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    user_id = str(uuid.uuid4())
    fake_db = DummySession()

    payload = TenantCreateContact(
        first_name="Alice",
        last_name="Smith",
        phones=[{"phone_raw": "123-456-7890"}],
        emails=[{"email": "alice@example.com"}],
    )

    fake_contact = _fake_contact_out(
        tenant_id=tenant_id,
        contact_id=uuid.uuid4(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        created_by=user_id,
        updated_by=user_id,
    )

    captured: dict = {}

    def fake_create_contact(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_contact

    monkeypatch.setattr(contact_service, "create_contact", fake_create_contact)

    result = create_contact_endpoint(
        tenant_id=tenant_id,
        contact_in=payload,
        db=fake_db,
        x_user=user_id,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["request"] == payload
    assert captured["created_by"] == user_id

    assert result == fake_contact


# ---------------------------------------------------------------------------
# get_contact_endpoint
# ---------------------------------------------------------------------------

def test_get_contact_calls_service(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    contact_id = uuid.uuid4()
    fake_db = DummySession()

    fake_contact = _fake_contact_out(
        tenant_id=tenant_id,
        contact_id=contact_id,
        first_name="Alice",
        last_name="Smith",
    )

    captured: dict = {}

    def fake_get_contact(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_contact

    monkeypatch.setattr(contact_service, "get_contact", fake_get_contact)

    result = get_contact_endpoint(
        tenant_id=tenant_id,
        contact_id=contact_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["contact_id"] == contact_id
    assert result == fake_contact


# ---------------------------------------------------------------------------
# patch_contact_endpoint
# ---------------------------------------------------------------------------

def test_patch_contact_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    contact_id = uuid.uuid4()
    user_id = str(uuid.uuid4())
    fake_db = DummySession()

    patch_request = JsonPatchRequest(
        operations=[JsonPatchOperation(op="replace", path="/first_name", value="Robert")]
    )

    fake_contact = _fake_contact_out(
        tenant_id=tenant_id,
        contact_id=contact_id,
        first_name="Robert",
        last_name="Smith",
        created_by="tester",
        updated_by=user_id,
    )

    captured: dict = {}

    def fake_patch_contact(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_contact

    monkeypatch.setattr(contact_service, "patch_contact", fake_patch_contact)

    result = patch_contact_endpoint(
        tenant_id=tenant_id,
        contact_id=contact_id,
        patch_request=patch_request,
        db=fake_db,
        x_user=user_id,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["contact_id"] == contact_id
    assert captured["patch_request"] == patch_request
    assert captured["updated_by"] == user_id
    assert result == fake_contact


# ---------------------------------------------------------------------------
# delete_contact_endpoint
# ---------------------------------------------------------------------------

def test_delete_contact_calls_service_and_returns_none(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    contact_id = uuid.uuid4()
    fake_db = DummySession()

    captured: dict = {"called": False}

    def fake_delete_contact(db, **kwargs):
        captured["called"] = True
        captured["db"] = db
        captured.update(kwargs)

    monkeypatch.setattr(contact_service, "delete_contact", fake_delete_contact)

    result = delete_contact_endpoint(
        tenant_id=tenant_id,
        contact_id=contact_id,
        db=fake_db,
    )

    assert captured["called"] is True
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["contact_id"] == contact_id
    assert result is None
