from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_assignment import (
    TenantCreateTicketAssignment,
    TicketAssignmentOut,
)
from app.domain.schemas.ticket_audit import TicketAuditOut
from app.domain.services import ticket_assignment_service, ticket_audit_service

from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_assignments_endpoint,
    create_ticket_assignment_endpoint,
    list_ticket_audits_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_assignment_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    assignment_id: uuid.UUID,
    assigned_group_id: Optional[uuid.UUID] = None,
    assigned_user_id: Optional[uuid.UUID] = None,
    assigned_by_user_id: Optional[uuid.UUID] = None,
    assigned_by_reason: Optional[str] = None,
    ai_session_id: Optional[uuid.UUID] = None,
) -> TicketAssignmentOut:
    return TicketAssignmentOut(
        id=assignment_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        assigned_group_id=assigned_group_id,
        assigned_user_id=assigned_user_id,
        assigned_by_user_id=assigned_by_user_id,
        assigned_by_reason=assigned_by_reason,
        ai_session_id=ai_session_id,
        created_at=None,
        created_by="tester",
    )


def _fake_audit_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    audit_id: uuid.UUID,
    event_type: str = "status_changed",
    actor_type: str = "agent",
    actor_contact_id: Optional[uuid.UUID] = None,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_display_name: Optional[str] = None,
    ai_session_id: Optional[uuid.UUID] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    occurred_at: Optional[str] = None,
) -> TicketAuditOut:
    return TicketAuditOut(
        id=audit_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_contact_id=actor_contact_id,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        ai_session_id=ai_session_id,
        before=before,
        after=after,
        occurred_at=occurred_at,
    )


def test_list_ticket_assignments_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_assignments = [
        _fake_assignment_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            assignment_id=uuid.uuid4(),
            assigned_group_id=uuid.uuid4(),
        )
    ]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_assignments

    monkeypatch.setattr(ticket_assignment_service, "list_ticket_assignments", fake_list)

    result = list_ticket_assignments_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_assignments


def test_create_ticket_assignment_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateTicketAssignment(
        assigned_group_id=uuid.uuid4(),
        assigned_user_id=None,
        assigned_by_user_id=uuid.uuid4(),
        assigned_by_reason="Initial assignment",
        ai_session_id=None,
    )
    fake_assignment = _fake_assignment_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        assignment_id=uuid.uuid4(),
        assigned_group_id=payload.assigned_group_id,
        assigned_user_id=payload.assigned_user_id,
        assigned_by_user_id=payload.assigned_by_user_id,
        assigned_by_reason=payload.assigned_by_reason,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_assignment

    monkeypatch.setattr(ticket_assignment_service, "create_ticket_assignment", fake_create)

    result = create_ticket_assignment_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        assignment_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_assignment


def test_list_ticket_audits_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_audits = [
        _fake_audit_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            audit_id=uuid.uuid4(),
            event_type="status_changed",
            actor_type="agent",
            after={"status": "open"},
        )
    ]
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_audits

    monkeypatch.setattr(ticket_audit_service, "list_ticket_audits", fake_list)

    result = list_ticket_audits_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        event_type="status_changed",
        actor_type="agent",
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert captured_kwargs["event_type"] == "status_changed"
    assert captured_kwargs["actor_type"] == "agent"
    assert result == fake_audits