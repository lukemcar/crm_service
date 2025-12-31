from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.company import (
    TenantCreateCompany,
    CompanyOut,
)
from app.domain.schemas.json_patch import JsonPatchRequest, JsonPatchOperation
from app.domain.services import company_service

# Route functions (tenant-scoped)
from app.api.routes.companies_tenant_route import (
    create_company_endpoint,
    get_company_endpoint,
    patch_company_endpoint,
    delete_company_endpoint,
)


class DummySession(Session):
    """Lightweight stand-in so type hints are happy without a real DB."""
    pass


def _fake_company_out(
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    name: str,
    website: str | None = None,
) -> CompanyOut:
    now = datetime.now(timezone.utc)
    return CompanyOut(
        id=company_id,
        tenant_id=tenant_id,
        name=name,
        website=website,
        industry=None,
        is_internal=False,
        created_at=now,
        updated_at=now,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# create_company_endpoint
# ---------------------------------------------------------------------------

def test_create_company_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    payload = TenantCreateCompany(
        name="ACME Corp",
        website="acme.com",
        industry=None,
        is_internal=False,
    )

    fake_company = _fake_company_out(
        tenant_id=tenant_id,
        company_id=uuid.uuid4(),
        name=payload.name,
        website=payload.website,
    )

    captured_kwargs: dict = {}

    # NOTE: the route calls company_service.create_company(db, **kwargs)
    # so our fake must accept the positional db arg.
    def fake_create_company(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_company

    monkeypatch.setattr(company_service, "create_company", fake_create_company)

    result = create_company_endpoint(
        tenant_id=tenant_id,
        company_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"

    assert result == fake_company


# ---------------------------------------------------------------------------
# get_company_endpoint
# ---------------------------------------------------------------------------

def test_get_company_calls_service(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    company_id = uuid.uuid4()
    fake_db = DummySession()

    fake_company = _fake_company_out(
        tenant_id=tenant_id,
        company_id=company_id,
        name="ACME Corp",
        website="acme.com",
    )

    captured_kwargs: dict = {}

    # NOTE: route calls company_service.get_company(db, tenant_id=..., company_id=...)
    def fake_get_company(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_company

    monkeypatch.setattr(company_service, "get_company", fake_get_company)

    result = get_company_endpoint(
        tenant_id=tenant_id,
        company_id=company_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["company_id"] == company_id

    assert result == fake_company


# ---------------------------------------------------------------------------
# patch_company_endpoint
# ---------------------------------------------------------------------------

def test_patch_company_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    company_id = uuid.uuid4()
    fake_db = DummySession()

    patch_request = JsonPatchRequest(
        operations=[
            JsonPatchOperation(op="replace", path="/name", value="New Name")
        ]
    )

    fake_company = _fake_company_out(
        tenant_id=tenant_id,
        company_id=company_id,
        name="New Name",
        website="acme.com",
    )

    captured_kwargs: dict = {}

    # NOTE: route calls company_service.patch_company(db, **kwargs)
    def fake_patch_company(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_company

    monkeypatch.setattr(company_service, "patch_company", fake_patch_company)

    result = patch_company_endpoint(
        tenant_id=tenant_id,
        company_id=company_id,
        patch_request=patch_request,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["company_id"] == company_id
    assert captured_kwargs["patch_request"] == patch_request
    assert captured_kwargs["updated_by"] == "tester"

    assert result == fake_company


# ---------------------------------------------------------------------------
# delete_company_endpoint
# ---------------------------------------------------------------------------

def test_delete_company_calls_service_and_returns_none(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    company_id = uuid.uuid4()
    fake_db = DummySession()

    captured: dict = {"called": False}

    # NOTE: route calls company_service.delete_company(db, **kwargs)
    def fake_delete_company(db, **kwargs):
        captured["called"] = True
        captured["db"] = db
        captured.update(kwargs)

    monkeypatch.setattr(company_service, "delete_company", fake_delete_company)

    result = delete_company_endpoint(
        tenant_id=tenant_id,
        company_id=company_id,
        db=fake_db,
    )

    assert captured["called"] is True
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["company_id"] == company_id

    assert result is None
