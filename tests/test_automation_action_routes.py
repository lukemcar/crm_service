"""
Tests for the Automation Action admin and tenant routes.

These tests validate that the new automation action endpoints delegate
requests to the service layer with the correct parameters and handle
audit headers appropriately.  The patterns mirror those used for
record watcher and support macro route tests.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionRead,
    AutomationActionUpdate,
)
import app.domain.services.automation_action_service as action_service

from app.api.routes.automation_actions_admin_route import (
    list_automation_actions_admin as list_actions_admin,
    create_automation_action_admin as create_action_admin,
    update_automation_action_admin as update_action_admin,
)
from app.api.routes.automation_actions_tenant_route import (
    list_automation_actions_endpoint as list_actions_tenant,
    create_automation_action_endpoint as create_action_tenant,
    update_automation_action_endpoint as update_action_tenant,
)


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""
    pass


def _fake_action_read(action_id: uuid.UUID, tenant_id: uuid.UUID) -> AutomationActionRead:
    """Construct a ``AutomationActionRead`` with minimal default values."""
    return AutomationActionRead(
        id=action_id,
        tenant_id=tenant_id,
        entity_type="deal",
        scope_type="record",
        record_type="deal",
        record_id=uuid.uuid4(),
        pipeline_id=None,
        pipeline_stage_id=None,
        list_id=None,
        trigger_event="created",
        condition_json=None,
        action_type="notify",
        config_json=None,
        priority=1,
        enabled=True,
        inherit_pipeline_actions=True,
        created_at=None,
        updated_at=None,
        created_by_user_id="tester",
        updated_by_user_id="tester",
    )


def test_list_automation_actions_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should pass parameters to the service."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_actions: List[AutomationActionRead] = [
        _fake_action_read(uuid.uuid4(), tenant_id)
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_actions, total

    monkeypatch.setattr(action_service, "list_automation_actions", fake_list)

    result = list_actions_admin(
        tenant_id=tenant_id,
        entity_type="deal",
        scope_type="record",
        limit=5,
        offset=0,
        db=fake_db,
    )
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["entity_type"] == "deal"
    assert captured["scope_type"] == "record"
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_actions)


def test_create_automation_action_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should forward audit info and tenant parameter."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AutomationActionCreate(
        entity_type="deal",
        scope_type="record",
        record_type="deal",
        record_id=uuid.uuid4(),
        trigger_event="created",
        action_type="notify",
    )
    fake_action = _fake_action_read(uuid.uuid4(), tenant_id)
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_action

    monkeypatch.setattr(action_service, "create_automation_action", fake_create)

    result = create_action_admin(
        tenant_id=tenant_id,
        action_in=payload,
        db=fake_db,
        x_user="creator",
    )
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["request"] == payload
    assert captured["created_by"] == "creator"
    assert result.tenant_id == tenant_id


def test_update_automation_action_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin update endpoint should pass identifiers and audit to the service."""
    tenant_id = uuid.uuid4()
    action_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AutomationActionUpdate(
        enabled=False,
    )
    fake_action = _fake_action_read(action_id, tenant_id)
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_action

    monkeypatch.setattr(action_service, "update_automation_action", fake_update)

    result = update_action_admin(
        action_id=action_id,
        tenant_id=tenant_id,
        action_update=payload,
        db=fake_db,
        x_user="updater",
    )
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["action_id"] == action_id
    assert captured["request"] == payload
    assert captured["updated_by"] == "updater"
    assert result.id == action_id


def test_list_automation_actions_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant list endpoint should pass parameters to the service."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_actions: List[AutomationActionRead] = [
        _fake_action_read(uuid.uuid4(), tenant_id)
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_actions, total

    monkeypatch.setattr(action_service, "list_automation_actions", fake_list)

    result = list_actions_tenant(
        tenant_id=tenant_id,
        entity_type="lead",
        scope_type=None,
        limit=None,
        offset=None,
        db=fake_db,
    )
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["entity_type"] == "lead"
    assert captured["scope_type"] is None
    assert result.total == total
    assert len(result.items) == len(fake_actions)


def test_create_automation_action_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant create endpoint should forward audit info."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AutomationActionCreate(
        entity_type="lead",
        scope_type="record",
        record_type="lead",
        record_id=uuid.uuid4(),
        trigger_event="created",
        action_type="notify",
    )
    fake_action = _fake_action_read(uuid.uuid4(), tenant_id)
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_action

    monkeypatch.setattr(action_service, "create_automation_action", fake_create)

    result = create_action_tenant(
        tenant_id=tenant_id,
        action_in=payload,
        db=fake_db,
        x_user="creator",
    )
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["request"] == payload
    assert captured["created_by"] == "creator"
    assert result.tenant_id == tenant_id


def test_update_automation_action_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant update endpoint should pass identifiers and audit to the service."""
    tenant_id = uuid.uuid4()
    action_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AutomationActionUpdate(
        priority=2,
    )
    fake_action = _fake_action_read(action_id, tenant_id)
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_action

    monkeypatch.setattr(action_service, "update_automation_action", fake_update)

    result = update_action_tenant(
        tenant_id=tenant_id,
        action_id=action_id,
        action_update=payload,
        db=fake_db,
        x_user="updater",
    )
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["action_id"] == action_id
    assert captured["request"] == payload
    assert captured["updated_by"] == "updater"
    assert result.id == action_id