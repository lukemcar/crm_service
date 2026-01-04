"""
Tests for the AutomationAction service functions.

These tests validate that the service layer correctly enforces tenant
matching, scope validation and not-found handling.  A lightweight
``DummySession`` class is used in place of a real SQLAlchemy session to
satisfy type hints and capture method invocations.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.models.automation_action import AutomationAction
from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionUpdate,
)
import app.domain.services.automation_action_service as action_service


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[AutomationAction] = []

    def query(self, model):  # type: ignore[override]
        # Return self to allow filter() chaining
        return self

    def filter(self, *args, **kwargs):  # type: ignore[override]
        return self

    def first(self):  # type: ignore[override]
        return None

    def add(self, instance):  # type: ignore[override]
        self.items.append(instance)

    def delete(self, instance):  # type: ignore[override]
        if instance in self.items:
            self.items.remove(instance)

    def commit(self):  # type: ignore[override]
        pass

    def refresh(self, instance):  # type: ignore[override]
        pass


def test_service_create_action_invalid_scope() -> None:
    """Creating an action with multiple scope identifiers should raise 400."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    action_in = AutomationActionCreate(
        tenant_id=tenant_id,
        entity_type="CONTACT",
        scope_type="RECORD",
        record_type="CONTACT",
        record_id=uuid.uuid4(),
        pipeline_id=uuid.uuid4(),  # Multiple scope identifiers provided
        trigger_event="created",
        action_type="notify",
    )
    with pytest.raises(HTTPException) as exc_info:
        action_service.service_create_action(
            db,
            tenant_id=tenant_id,
            action_in=action_in,
            created_by_user_id=None,
        )
    assert exc_info.value.status_code == 400


def test_service_create_action_tenant_mismatch() -> None:
    """Creating an action with mismatched tenant IDs should raise 400."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    action_in = AutomationActionCreate(
        tenant_id=other_tenant,
        entity_type="DEAL",
        scope_type="RECORD",
        record_type="DEAL",
        record_id=uuid.uuid4(),
        trigger_event="updated",
        action_type="update_field",
    )
    with pytest.raises(HTTPException) as exc_info:
        action_service.service_create_action(
            db,
            tenant_id=tenant_id,
            action_in=action_in,
            created_by_user_id=None,
        )
    assert exc_info.value.status_code == 400


def test_service_update_action_scope_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Updating an action to set an additional scope identifier should raise 400."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    action_id = uuid.uuid4()
    # Create an existing AutomationAction with record scope only
    existing_action = AutomationAction(
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
    )
    # Stub query.first to return the existing action
    def fake_first():
        return existing_action
    monkeypatch.setattr(db, "first", fake_first)
    # Prepare update that attempts to add a pipeline_id (invalid, would result in two scope identifiers)
    update_in = AutomationActionUpdate(pipeline_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc_info:
        action_service.service_update_action(
            db,
            tenant_id=tenant_id,
            action_id=action_id,
            update_in=update_in,
            updated_by_user_id=None,
        )
    assert exc_info.value.status_code == 400


def test_service_delete_action_not_found() -> None:
    """Deleting a non‑existent action should raise 404."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    action_id = uuid.uuid4()
    # No action in session; first() returns None
    with pytest.raises(HTTPException) as exc_info:
        action_service.service_delete_action(
            db,
            tenant_id=tenant_id,
            action_id=action_id,
            deleted_by_user_id=None,
        )
    assert exc_info.value.status_code == 404