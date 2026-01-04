"""
Tests for the AutomationAction admin routes.

These tests ensure that the admin endpoints for automation actions call
the appropriate service functions with the correct parameters and
propagate audit identifiers from headers.  Dummy stubs are used in
place of real database sessions and service implementations.
"""

from __future__ import annotations

import uuid
from typing import Optional, Tuple, List, Dict

import pytest
from sqlalchemy.orm import Session

from app.domain.models.automation_action import AutomationAction
from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionUpdate,
    AutomationActionRead,
)
import app.domain.services.automation_action_service as action_service

from app.api.routes.automation_actions_admin_route import (
    list_automation_actions,
    create_automation_action,
    update_automation_action,
    delete_automation_action,
)


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""
    pass


def _fake_action_read(*, tenant_id: uuid.UUID, action_id: uuid.UUID) -> AutomationActionRead:
    """Helper to build a fake AutomationActionRead with random attributes."""
    return AutomationActionRead(
        id=action_id,
        tenant_id=tenant_id,
        entity_type="CONTACT",
        scope_type="RECORD",
        record_type="CONTACT",
        record_id=uuid.uuid4(),
        pipeline_id=None,
        pipeline_stage_id=None,
        list_id=None,
        trigger_event="created",
        condition_json=None,
        action_type="notify",
        config_json=None,
        priority=0,
        enabled=True,
        inherit_pipeline_actions=True,
        created_at=None,
        updated_at=None,
    )


def test_admin_list_actions_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should pass tenant filter and pagination to the service."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    limit = 5
    offset = 0
    fake_actions: List[AutomationAction] = []
    total = 0
    captured: Dict[str, object] = {}

    def fake_list(db, **kwargs) -> Tuple[List[AutomationAction], int]:
        captured["db"] = db
        captured.update(kwargs)
        return fake_actions, total

    monkeypatch.setattr(action_service, "service_list_actions", fake_list)

    result = list_automation_actions(
        tenant_id=tenant_id,
        entity_type=None,
        scope_type=None,
        enabled=None,
        limit=limit,
        offset=offset,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["entity_type"] is None
    assert captured["scope_type"] is None
    assert captured["enabled"] is None
    assert captured["limit"] == limit
    assert captured["offset"] == offset
    assert result.total == total
    assert len(result.items) == len(fake_actions)


def test_admin_create_action_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should forward tenant and body parameters and audit user ID."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    action_in = AutomationActionCreate(
        tenant_id=tenant_id,
        entity_type="DEAL",
        scope_type="RECORD",
        record_type="DEAL",
        record_id=uuid.uuid4(),
        trigger_event="created",
        action_type="update",
    )
    fake_action = _fake_action_read(tenant_id=tenant_id, action_id=uuid.uuid4())
    captured: Dict[str, object] = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_action

    monkeypatch.setattr(action_service, "service_create_action", fake_create)

    result = create_automation_action(
        tenant_id=tenant_id,
        action_in=action_in,
        x_user_id=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    # tenant_id should remain unchanged on the update
    assert captured["tenant_id"] == tenant_id
    assert captured["action_in"].tenant_id == tenant_id
    assert result.id == fake_action.id
    assert result.tenant_id == fake_action.tenant_id


def test_admin_update_action_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin update endpoint should forward identifiers and body to the service."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    action_id = uuid.uuid4()
    update_in = AutomationActionUpdate(
        enabled=False,
    )
    fake_action = _fake_action_read(tenant_id=tenant_id, action_id=action_id)
    captured: Dict[str, object] = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_action

    monkeypatch.setattr(action_service, "service_update_action", fake_update)

    result = update_automation_action(
        action_id=action_id,
        tenant_id=tenant_id,
        action_in=update_in,
        x_user_id=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["action_id"] == action_id
    assert captured["update_in"] is update_in
    assert result.id == fake_action.id


def test_admin_delete_action_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should forward identifiers to the service."""
    fake_db = DummySession()
    tenant_id = uuid.uuid4()
    action_id = uuid.uuid4()
    captured: Dict[str, object] = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(action_service, "service_delete_action", fake_delete)

    response = delete_automation_action(
        action_id=action_id,
        tenant_id=tenant_id,
        x_user_id=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["action_id"] == action_id
    assert response.status_code == 204