"""
Tests for ticket task mirror and AI work ref nested routes.

These tests verify that the tenant and admin nested endpoints for
task mirrors and AI work references delegate correctly to the
service layer and propagate request parameters.  Only a subset of
paths are tested here; full coverage can be achieved by following
this pattern for additional endpoints.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_task_mirror import TicketTaskMirrorOut
from app.domain.schemas.ticket_ai_work_ref import TicketAiWorkRefOut
from app.domain.services import (
    ticket_task_mirror_service,
    ticket_ai_work_ref_service,
)

from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_task_mirrors_endpoint,
    get_ticket_task_mirror_endpoint,
    list_ticket_ai_work_refs_endpoint,
    get_ticket_ai_work_ref_endpoint,
)

from app.api.routes.tickets_admin_nested_routes import (
    list_ticket_task_mirrors_admin_endpoint,
    get_ticket_task_mirror_admin_endpoint,
    list_ticket_ai_work_refs_admin_endpoint,
    get_ticket_ai_work_ref_admin_endpoint,
)


class DummySession(Session):
    """Lightweight stand-in to satisfy type hints without a real DB."""
    pass


def _fake_task_mirror_out(tenant_id: uuid.UUID, ticket_id: uuid.UUID, mirror_id: uuid.UUID) -> TicketTaskMirrorOut:
    return TicketTaskMirrorOut(
        id=mirror_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        orchestration_task_id="task",
        orchestration_process_instance_id=None,
        orchestration_process_definition_key=None,
        name="Task",
        description=None,
        status="open",
        due_at=None,
        assigned_user_id=None,
        assigned_group_id=None,
        created_at=None,
        updated_at=None,
    )


def _fake_ai_work_ref_out(tenant_id: uuid.UUID, ticket_id: uuid.UUID, ref_id: uuid.UUID) -> TicketAiWorkRefOut:
    return TicketAiWorkRefOut(
        id=ref_id,
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


def test_list_ticket_task_mirrors_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_tasks = [_fake_task_mirror_out(tenant_id, ticket_id, uuid.uuid4())]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_tasks, len(fake_tasks)

    monkeypatch.setattr(ticket_task_mirror_service, "list_ticket_task_mirrors", fake_list)

    result = list_ticket_task_mirrors_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status="open",
        limit=10,
        offset=5,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["status"] == "open"
    assert captured_kwargs["limit"] == 10
    assert captured_kwargs["offset"] == 5
    # Convert to list of out models for comparison
    assert result == fake_tasks


def test_get_ticket_task_mirror_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    mirror_id = uuid.uuid4()
    fake_db = DummySession()
    fake_mirror = _fake_task_mirror_out(tenant_id, ticket_id, mirror_id)

    def fake_get(db, *, tenant_id: uuid.UUID, mirror_id: uuid.UUID):
        assert tenant_id == tenant_id  # ensure parameters match
        assert mirror_id == mirror_id
        return fake_mirror

    monkeypatch.setattr(ticket_task_mirror_service, "get_ticket_task_mirror", fake_get)

    result = get_ticket_task_mirror_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        mirror_id=mirror_id,
        db=fake_db,
    )

    assert result == fake_mirror


def test_list_ticket_ai_work_refs_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_refs = [_fake_ai_work_ref_out(tenant_id, ticket_id, uuid.uuid4())]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_refs, len(fake_refs)

    monkeypatch.setattr(ticket_ai_work_ref_service, "list_ticket_ai_work_refs", fake_list)

    result = list_ticket_ai_work_refs_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        agent_key="agent",
        limit=20,
        offset=0,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["agent_key"] == "agent"
    assert captured_kwargs["limit"] == 20
    assert captured_kwargs["offset"] == 0
    assert result == fake_refs


def test_get_ticket_ai_work_ref_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    ref_id = uuid.uuid4()
    fake_db = DummySession()
    fake_ref = _fake_ai_work_ref_out(tenant_id, ticket_id, ref_id)

    def fake_get(db, *, tenant_id: uuid.UUID, ref_id: uuid.UUID):
        assert tenant_id == tenant_id
        assert ref_id == ref_id
        return fake_ref

    monkeypatch.setattr(ticket_ai_work_ref_service, "get_ticket_ai_work_ref", fake_get)

    result = get_ticket_ai_work_ref_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ref_id=ref_id,
        db=fake_db,
    )

    assert result == fake_ref


def test_admin_list_task_mirrors_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_tasks = [_fake_task_mirror_out(tenant_id, ticket_id, uuid.uuid4())]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_tasks, len(fake_tasks)

    monkeypatch.setattr(ticket_task_mirror_service, "list_ticket_task_mirrors", fake_list)

    result = list_ticket_task_mirrors_admin_endpoint(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        status="open",
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["status"] == "open"
    assert captured_kwargs["limit"] == 5
    assert captured_kwargs["offset"] == 0
    # Response is list of models; convert
    assert result == [TicketTaskMirrorOut.model_validate(t, from_attributes=True) for t in fake_tasks]


def test_admin_get_task_mirror_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    mirror_id = uuid.uuid4()
    fake_db = DummySession()
    fake_mirror = _fake_task_mirror_out(tenant_id, ticket_id, mirror_id)

    def fake_get(db, *, tenant_id: uuid.UUID, mirror_id: uuid.UUID):
        assert tenant_id == tenant_id
        assert mirror_id == mirror_id
        return fake_mirror

    monkeypatch.setattr(ticket_task_mirror_service, "get_ticket_task_mirror", fake_get)

    result = get_ticket_task_mirror_admin_endpoint(
        ticket_id=ticket_id,
        mirror_id=mirror_id,
        tenant_id=tenant_id,
        db=fake_db,
    )
    assert result == TicketTaskMirrorOut.model_validate(fake_mirror, from_attributes=True)


def test_admin_list_ai_work_refs_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_refs = [_fake_ai_work_ref_out(tenant_id, ticket_id, uuid.uuid4())]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_refs, len(fake_refs)

    monkeypatch.setattr(ticket_ai_work_ref_service, "list_ticket_ai_work_refs", fake_list)

    result = list_ticket_ai_work_refs_admin_endpoint(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        agent_key="agent",
        limit=5,
        offset=0,
        db=fake_db,
    )
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["agent_key"] == "agent"
    assert captured_kwargs["limit"] == 5
    assert captured_kwargs["offset"] == 0
    assert result == [TicketAiWorkRefOut.model_validate(r, from_attributes=True) for r in fake_refs]


def test_admin_get_ai_work_ref_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    ref_id = uuid.uuid4()
    fake_db = DummySession()
    fake_ref = _fake_ai_work_ref_out(tenant_id, ticket_id, ref_id)

    def fake_get(db, *, tenant_id: uuid.UUID, ref_id: uuid.UUID):
        assert tenant_id == tenant_id
        assert ref_id == ref_id
        return fake_ref

    monkeypatch.setattr(ticket_ai_work_ref_service, "get_ticket_ai_work_ref", fake_get)

    result = get_ticket_ai_work_ref_admin_endpoint(
        ticket_id=ticket_id,
        ref_id=ref_id,
        tenant_id=tenant_id,
        db=fake_db,
    )
    assert result == TicketAiWorkRefOut.model_validate(fake_ref, from_attributes=True)