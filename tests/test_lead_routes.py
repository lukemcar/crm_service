from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.lead import CreateLead, LeadOut
from app.api.routes.leads_tenant_route import create_lead_endpoint
from app.api.routes.leads_admin_route import create_lead_admin
import app.domain.services.lead_service as lead_service


class DummySession(Session):
    """Lightweight stand-in so type hints are happy without a real DB."""
    pass


def _fake_lead_out(
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    first_name: str,
    last_name: str,
    created_by: str = "tester",
    updated_by: str = "tester",
    owned_by_user_id: uuid.UUID | None = None,
    owned_by_group_id: uuid.UUID | None = None,
) -> LeadOut:
    now = datetime.now(timezone.utc)
    return LeadOut(
        id=lead_id,
        tenant_id=tenant_id,
        first_name=first_name,
        middle_name=None,
        last_name=last_name,
        source=None,
        lead_data=None,
        owned_by_user_id=owned_by_user_id,
        owned_by_group_id=owned_by_group_id,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


def test_create_lead_tenant_route_propagates_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure the tenant create lead endpoint forwards the owned_by_user_id field and audit user
    to the service layer when creating a lead.
    """
    tenant_id = uuid.uuid4()
    user_id = str(uuid.uuid4())
    owner_user_id = uuid.uuid4()
    fake_db = DummySession()

    payload = CreateLead(
        first_name="Alice",
        last_name="Smith",
        lead_data=None,
        owned_by_user_id=owner_user_id,
    )

    fake_lead = _fake_lead_out(
        tenant_id=tenant_id,
        lead_id=uuid.uuid4(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        created_by=user_id,
        updated_by=user_id,
        owned_by_user_id=owner_user_id,
        owned_by_group_id=None,
    )

    captured: dict = {}

    def fake_create_lead(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_lead

    monkeypatch.setattr(lead_service, "create_lead", fake_create_lead)

    result = create_lead_endpoint(
        tenant_id=tenant_id,
        lead_in=payload,
        db=fake_db,
        x_user=user_id,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["lead_in"] == payload
    assert captured["created_user"] == user_id
    assert result == fake_lead


def test_create_lead_admin_route_propagates_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure the admin create lead endpoint forwards the owned_by_group_id field and audit user
    to the service layer when creating a lead.
    """
    tenant_id = uuid.uuid4()
    user_id = str(uuid.uuid4())
    owner_group_id = uuid.uuid4()
    fake_db = DummySession()

    payload = CreateLead(
        first_name="Bob",
        last_name="Jones",
        lead_data=None,
        owned_by_group_id=owner_group_id,
    )

    fake_lead = _fake_lead_out(
        tenant_id=tenant_id,
        lead_id=uuid.uuid4(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        created_by=user_id,
        updated_by=user_id,
        owned_by_user_id=None,
        owned_by_group_id=owner_group_id,
    )

    captured: dict = {}

    def fake_service_create_lead(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_lead

    # Patch the service alias used by admin route
    monkeypatch.setattr(lead_service, "service_create_lead", fake_service_create_lead)

    result = create_lead_admin(
        tenant_id=tenant_id,
        lead_in=payload,
        db=fake_db,
        x_user=user_id,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["lead_in"] == payload
    assert captured["created_user"] == user_id
    assert result == fake_lead