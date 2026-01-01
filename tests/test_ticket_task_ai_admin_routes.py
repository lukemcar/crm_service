"""
Tests for ticket task mirror and AI work reference admin upsert routes.

These tests verify that the admin-level routes for upserting and deleting
task mirrors and AI work references delegate correctly to the service
layer and propagate the correct parameters, including audit information
from the ``X-User`` header.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_task_mirror import AdminUpsertTicketTaskMirror, TicketTaskMirrorOut
from app.domain.schemas.ticket_ai_work_ref import AdminUpsertTicketAiWorkRef, TicketAiWorkRefOut
from app.domain.services import (
    ticket_task_mirror_service,
    ticket_ai_work_ref_service,
)

from app.api.routes.ticket_task_mirrors_admin_route import (
    upsert_ticket_task_mirror_admin,
    delete_ticket_task_mirror_admin,
)

from app.api.routes.ticket_ai_work_refs_admin_route import (
    upsert_ticket_ai_work_ref_admin,
    delete_ticket_ai_work_ref_admin,
)


class DummySession(Session):
    """Lightweight stand-in to satisfy type hints without a real DB."""
    pass


def test_upsert_ticket_task_mirror_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    mirror_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AdminUpsertTicketTaskMirror(
        id=None,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        orchestration_task_id="task",
        name="Task",
        orchestration_process_instance_id=None,
        orchestration_process_definition_key=None,
        description=None,
        status="open",
        due_at=None,
        assigned_user_id=None,
        assigned_group_id=None,
    )
    fake_mirror = TicketTaskMirrorOut(
        id=mirror_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        orchestration_task_id=payload.orchestration_task_id,
        orchestration_process_instance_id=None,
        orchestration_process_definition_key=None,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        due_at=None,
        assigned_user_id=None,
        assigned_group_id=None,
        created_at=None,
        updated_at=None,
    )
    captured_args: dict = {}

    def fake_upsert(db, *, tenant_id: uuid.UUID, request: AdminUpsertTicketTaskMirror, updated_by: str):
        captured_args["db"] = db
        captured_args["tenant_id"] = tenant_id
        captured_args["request"] = request
        captured_args["updated_by"] = updated_by
        return fake_mirror

    monkeypatch.setattr(ticket_task_mirror_service, "upsert_ticket_task_mirror", fake_upsert)

    result = upsert_ticket_task_mirror_admin(
        mirror_id=mirror_id,
        request=payload,
        db=fake_db,
        x_user="admin_user",
    )

    assert captured_args["db"] is fake_db
    assert captured_args["tenant_id"] == tenant_id
    assert captured_args["request"].id == mirror_id
    assert captured_args["updated_by"] == "admin_user"
    assert result == fake_mirror


def test_delete_ticket_task_mirror_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    mirror_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_args: dict = {}

    def fake_delete(db, *, tenant_id: uuid.UUID, mirror_id: uuid.UUID):
        captured_args["db"] = db
        captured_args["tenant_id"] = tenant_id
        captured_args["mirror_id"] = mirror_id
        return None

    monkeypatch.setattr(ticket_task_mirror_service, "delete_ticket_task_mirror", fake_delete)

    result = delete_ticket_task_mirror_admin(
        mirror_id=mirror_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="admin_user",
    )

    assert captured_args["db"] is fake_db
    assert captured_args["tenant_id"] == tenant_id
    assert captured_args["mirror_id"] == mirror_id
    assert result is None


def test_upsert_ticket_ai_work_ref_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ref_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AdminUpsertTicketAiWorkRef(
        id=None,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ai_session_id=uuid.uuid4(),
        agent_key="agent",
        purpose="triage",
        status="started",
        outcome=None,
        confidence=None,
        requested_at=None,
        completed_at=None,
        created_by=None,
    )
    fake_ref = TicketAiWorkRefOut(
        id=ref_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ai_session_id=payload.ai_session_id,
        agent_key=payload.agent_key,
        purpose=payload.purpose,
        status=payload.status,
        outcome=payload.outcome,
        confidence=payload.confidence,
        requested_at=None,
        completed_at=None,
        created_by=None,
    )
    captured_args: dict = {}

    def fake_upsert(db, *, tenant_id: uuid.UUID, request: AdminUpsertTicketAiWorkRef, updated_by: str):
        captured_args["db"] = db
        captured_args["tenant_id"] = tenant_id
        captured_args["request"] = request
        captured_args["updated_by"] = updated_by
        return fake_ref

    monkeypatch.setattr(ticket_ai_work_ref_service, "upsert_ticket_ai_work_ref", fake_upsert)

    result = upsert_ticket_ai_work_ref_admin(
        ref_id=ref_id,
        request=payload,
        db=fake_db,
        x_user="admin_user",
    )

    assert captured_args["db"] is fake_db
    assert captured_args["tenant_id"] == tenant_id
    assert captured_args["request"].id == ref_id
    assert captured_args["updated_by"] == "admin_user"
    assert result == fake_ref


def test_delete_ticket_ai_work_ref_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ref_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_args: dict = {}

    def fake_delete(db, *, tenant_id: uuid.UUID, ref_id: uuid.UUID):
        captured_args["db"] = db
        captured_args["tenant_id"] = tenant_id
        captured_args["ref_id"] = ref_id
        return None

    monkeypatch.setattr(ticket_ai_work_ref_service, "delete_ticket_ai_work_ref", fake_delete)

    result = delete_ticket_ai_work_ref_admin(
        ref_id=ref_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="admin_user",
    )

    assert captured_args["db"] is fake_db
    assert captured_args["tenant_id"] == tenant_id
    assert captured_args["ref_id"] == ref_id
    assert result is None