"""Tests for the Deal admin and tenant routes.

These tests verify that the refactored deal endpoints correctly call into
the service layer with appropriate parameters and use the ``X-User`` header
to populate audit fields.  Pipeline and stage validations are stubbed
out via monkeypatching so that unit tests can focus on argument
propagation rather than business validation.  A ``DummySession`` avoids
requiring a real database connection.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.deal import DealCreate, DealUpdate, DealRead
import app.domain.services.deal_service as deal_service
import app.domain.services.pipeline_service as pipeline_service
import app.domain.services.pipeline_stage_service as pipeline_stage_service

from app.api.routes.deals_admin_route import (
    list_deals_admin,
    create_deal_admin,
    delete_deal_admin,
)
from app.api.routes.deals_tenant_route import (
    list_deals_tenant,
    create_deal_tenant,
    delete_deal_tenant,
)


class DummySession(Session):
    """Lightweight stand‑in for SQLAlchemy Session."""

    pass


def _fake_deal_read(
    tenant_id: uuid.UUID,
    deal_id: uuid.UUID,
    name: str = "Opportunity",
    pipeline_id: Optional[uuid.UUID] = None,
    stage_id: Optional[uuid.UUID] = None,
    amount: Optional[float] = None,
    probability: Optional[float] = None,
    *,
    owned_by_user_id: uuid.UUID | None = None,
    owned_by_group_id: uuid.UUID | None = None,
    assigned_user_id: uuid.UUID | None = None,
    assigned_group_id: uuid.UUID | None = None,
    deal_type: str | None = None,
    forecast_probability: float | None = None,
    close_date: date | None = None,
    created_by: str = "tester",
    updated_by: str = "tester",
) -> DealRead:
    now = datetime.now(timezone.utc)
    return DealRead(
        id=deal_id,
        tenant_id=tenant_id,
        name=name,
        amount=amount,
        expected_close_date=None,
        pipeline_id=pipeline_id or uuid.uuid4(),
        stage_id=stage_id or uuid.uuid4(),
        probability=probability,
        owned_by_user_id=owned_by_user_id,
        owned_by_group_id=owned_by_group_id,
        assigned_user_id=assigned_user_id,
        assigned_group_id=assigned_group_id,
        deal_type=deal_type,
        forecast_probability=forecast_probability,
        close_date=close_date,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


# Helper dummy objects for pipeline and stage
class _DummyPipeline:
    def __init__(self, id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        self.id = id
        self.tenant_id = tenant_id


class _DummyStage:
    def __init__(self, id: uuid.UUID, pipeline_id: uuid.UUID) -> None:
        self.id = id
        self.pipeline_id = pipeline_id


# ---------------------------------------------------------------------------
# Admin list
# ---------------------------------------------------------------------------


def test_list_deals_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    fake_deals: List[DealRead] = [
        _fake_deal_read(
            tenant_id=tenant_id,
            deal_id=uuid.uuid4(),
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_deals, total

    monkeypatch.setattr(deal_service, "service_list_deals", fake_list)

    result = list_deals_admin(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["stage_id"] == stage_id
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_deals)


# ---------------------------------------------------------------------------
# Admin create
# ---------------------------------------------------------------------------


def test_create_deal_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    owner_user = uuid.uuid4()
    assignee_user = uuid.uuid4()
    payload = DealCreate(
        name="Big Deal",
        pipeline_id=uuid.uuid4(),
        stage_id=uuid.uuid4(),
        amount=1000.0,
        expected_close_date=None,
        owned_by_user_id=owner_user,
        assigned_user_id=assignee_user,
        deal_type="new_business",
        forecast_probability=0.85,
        close_date=date(2026, 1, 1),
    )
    fake_deal = _fake_deal_read(
        tenant_id=tenant_id,
        deal_id=uuid.uuid4(),
        name=payload.name,
        pipeline_id=payload.pipeline_id,
        stage_id=payload.stage_id,
        owned_by_user_id=owner_user,
        assigned_user_id=assignee_user,
        deal_type=payload.deal_type,
        forecast_probability=payload.forecast_probability,
        close_date=payload.close_date,
    )
    captured: dict = {}

    # Stub pipeline and stage lookups to succeed
    monkeypatch.setattr(
        pipeline_service,
        "get_pipeline",
        lambda db, pipeline_id, tenant_id: _DummyPipeline(pipeline_id, tenant_id),
    )
    monkeypatch.setattr(
        pipeline_stage_service,
        "get_stage",
        lambda db, stage_id: _DummyStage(stage_id, payload.pipeline_id),
    )

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_deal

    monkeypatch.setattr(deal_service, "service_create_deal", fake_create)

    result = create_deal_admin(
        tenant_id=tenant_id,
        deal_in=payload,
        db=fake_db,
        x_user="seller",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["deal_in"] == payload
    assert captured["created_user"] == "seller"
    assert result.id == fake_deal.id
    # Ensure ownership and assignment fields are forwarded through service call
    assert captured["deal_in"].owned_by_user_id == owner_user
    assert captured["deal_in"].assigned_user_id == assignee_user


# ---------------------------------------------------------------------------
# Tenant list
# ---------------------------------------------------------------------------


def test_list_deals_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    fake_deals: List[DealRead] = [
        _fake_deal_read(
            tenant_id=tenant_id,
            deal_id=uuid.uuid4(),
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_deals, total

    monkeypatch.setattr(deal_service, "service_list_deals", fake_list)

    result = list_deals_tenant(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["stage_id"] == stage_id
    assert captured["limit"] is None
    assert captured["offset"] is None
    assert result.total == total
    assert len(result.items) == len(fake_deals)


# ---------------------------------------------------------------------------
# Tenant create
# ---------------------------------------------------------------------------


def test_create_deal_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = DealCreate(
        name="Big Deal",
        pipeline_id=uuid.uuid4(),
        stage_id=uuid.uuid4(),
        amount=1000.0,
        expected_close_date=None,
    )
    fake_deal = _fake_deal_read(
        tenant_id=tenant_id,
        deal_id=uuid.uuid4(),
        name=payload.name,
        pipeline_id=payload.pipeline_id,
        stage_id=payload.stage_id,
    )
    captured: dict = {}

    # Stub pipeline and stage lookups to succeed
    monkeypatch.setattr(
        pipeline_service,
        "get_pipeline",
        lambda db, pipeline_id, tenant_id: _DummyPipeline(pipeline_id, tenant_id),
    )
    monkeypatch.setattr(
        pipeline_stage_service,
        "get_stage",
        lambda db, stage_id: _DummyStage(stage_id, payload.pipeline_id),
    )

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_deal

    monkeypatch.setattr(deal_service, "service_create_deal", fake_create)

    result = create_deal_tenant(
        tenant_id=tenant_id,
        deal_in=payload,
        db=fake_db,
        x_user="seller",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["deal_in"] == payload
    assert captured["created_user"] == "seller"
    assert result.id == fake_deal.id


# ---------------------------------------------------------------------------
# Delete endpoints
# ---------------------------------------------------------------------------


def test_delete_deal_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    deal_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(deal_service, "service_delete_deal", fake_delete)

    result = delete_deal_admin(
        tenant_id=tenant_id,
        deal_id=deal_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["deal_id"] == deal_id
    # Returns a Response object with status 204
    assert result.status_code == 204


def test_delete_deal_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    deal_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(deal_service, "service_delete_deal", fake_delete)

    result = delete_deal_tenant(
        tenant_id=tenant_id,
        deal_id=deal_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["deal_id"] == deal_id
    assert result.status_code == 204