"""
Tests for the AutomationActionExecution service functions.

These tests validate that the service layer correctly enforces tenant
matching, status validation, and not-found handling for execution
records.  A lightweight ``DummySession`` class is used to stand in for
a real SQLAlchemy session, and monkeypatching is employed to stub
query results.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.models.automation_action_execution import AutomationActionExecution
from app.domain.schemas.automation_action_execution import (
    AutomationActionExecutionCreate,
    AutomationActionExecutionUpdate,
)
import app.domain.services.automation_action_execution_service as exe_service


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[AutomationActionExecution] = []

    def query(self, model):  # type: ignore[override]
        return self

    def filter(self, *args, **kwargs):  # type: ignore[override]
        return self

    def first(self):  # type: ignore[override]
        return None

    def add(self, instance):  # type: ignore[override]
        self.items.append(instance)

    def commit(self):  # type: ignore[override]
        pass

    def refresh(self, instance):  # type: ignore[override]
        pass


def test_service_create_execution_tenant_mismatch() -> None:
    """Creating an execution with mismatched tenant IDs should raise 400."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    execution_in = AutomationActionExecutionCreate(
        tenant_id=other_tenant,
        action_id=uuid.uuid4(),
        entity_type="CONTACT",
        entity_id=uuid.uuid4(),
        execution_key="key1",
        status="PENDING",
    )
    with pytest.raises(HTTPException) as exc_info:
        exe_service.service_create_execution(
            db,
            tenant_id=tenant_id,
            execution_in=execution_in,
        )
    assert exc_info.value.status_code == 400


def test_service_update_execution_invalid_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Updating an execution with an invalid status should raise 400."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    execution_id = uuid.uuid4()
    # Existing execution stub
    existing_exe = AutomationActionExecution(
        id=execution_id,
        tenant_id=tenant_id,
        action_id=uuid.uuid4(),
        entity_type="CONTACT",
        entity_id=uuid.uuid4(),
        pipeline_id=None,
        from_stage_id=None,
        to_stage_id=None,
        list_id=None,
        trigger_event=None,
        execution_key="key1",
        status="PENDING",
        response_code=None,
        response_body=None,
        error_message=None,
    )
    # Stub query.first to return existing execution
    def fake_first():
        return existing_exe
    monkeypatch.setattr(db, "first", fake_first)
    update_in = AutomationActionExecutionUpdate(status="INVALID_STATUS")
    with pytest.raises(HTTPException) as exc_info:
        exe_service.service_update_execution(
            db,
            tenant_id=tenant_id,
            execution_id=execution_id,
            update_in=update_in,
        )
    assert exc_info.value.status_code == 400


def test_service_update_execution_not_found() -> None:
    """Updating a non‑existent execution should raise 404."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    execution_id = uuid.uuid4()
    update_in = AutomationActionExecutionUpdate(status="SUCCEEDED")
    with pytest.raises(HTTPException) as exc_info:
        exe_service.service_update_execution(
            db,
            tenant_id=tenant_id,
            execution_id=execution_id,
            update_in=update_in,
        )
    assert exc_info.value.status_code == 404