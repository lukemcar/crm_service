"""
Tests for ticket reporting primitives nested admin routes.

This module verifies that the admin endpoints for ticket metrics and
ticket status duration correctly delegate to the service layer and
propagate the ``X-User`` header to the service layer for audit.
"""

from __future__ import annotations

import uuid
from typing import List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_metrics import (
    AdminCreateTicketMetrics,
    TicketMetricsUpdate,
    TicketMetricsOut,
)
from app.domain.schemas.ticket_status_duration import (
    AdminCreateTicketStatusDuration,
    AdminUpdateTicketStatusDuration,
    TicketStatusDurationOut,
)
from app.domain.services import ticket_metrics_service, ticket_status_duration_service
from app.api.routes.tickets_admin_nested_routes import (
    list_ticket_metrics_admin_endpoint,
    create_ticket_metrics_admin_endpoint,
    get_ticket_metrics_admin_endpoint,
    update_ticket_metrics_admin_endpoint,
    delete_ticket_metrics_admin_endpoint,
    list_ticket_status_durations_admin_endpoint,
    create_ticket_status_duration_admin_endpoint,
    get_ticket_status_duration_admin_endpoint,
    update_ticket_status_duration_admin_endpoint,
    delete_ticket_status_duration_admin_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""
    pass


def _fake_metrics_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    metrics_id: uuid.UUID,
    reply_count: int = 0,
    reopen_count: int = 0,
) -> TicketMetricsOut:
    return TicketMetricsOut(
        id=metrics_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        reply_count=reply_count,
        reopen_count=reopen_count,
        created_at=None,
        updated_at=None,
        updated_by="tester",
    )


def _fake_status_duration_out(
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    duration_id: uuid.UUID,
    status: str = "new",
) -> TicketStatusDurationOut:
    return TicketStatusDurationOut(
        id=duration_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=status,
        started_at=None,
        ended_at=None,
        duration_seconds=None,
        created_at=None,
        created_by="tester",
    )


def test_list_ticket_metrics_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_metrics: List[TicketMetricsOut] = [
        _fake_metrics_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            metrics_id=uuid.uuid4(),
            reply_count=2,
            reopen_count=1,
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_metrics, total

    monkeypatch.setattr(ticket_metrics_service, "list_ticket_metrics", fake_list)

    result = list_ticket_metrics_admin_endpoint(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_metrics


def test_create_ticket_metrics_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AdminCreateTicketMetrics(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        reply_count=1,
        reopen_count=0,
    )
    fake_metric = _fake_metrics_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        metrics_id=uuid.uuid4(),
        reply_count=payload.reply_count,
        reopen_count=payload.reopen_count,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_metric

    monkeypatch.setattr(ticket_metrics_service, "create_ticket_metrics", fake_create)

    result = create_ticket_metrics_admin_endpoint(
        ticket_id=ticket_id,
        metrics_in=payload,
        db=fake_db,
        x_user="admin_user",
    )

    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "admin_user"
    assert result == fake_metric


def test_update_ticket_metrics_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    metrics_id = uuid.uuid4()
    fake_db = DummySession()
    update = TicketMetricsUpdate(reply_count=5)
    fake_metric = _fake_metrics_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        metrics_id=metrics_id,
        reply_count=update.reply_count,
        reopen_count=0,
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_metric

    monkeypatch.setattr(ticket_metrics_service, "update_ticket_metrics", fake_update)

    result = update_ticket_metrics_admin_endpoint(
        ticket_id=ticket_id,
        metrics_id=metrics_id,
        metrics_update=update,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="system_user",
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["metrics_id"] == metrics_id
    assert captured_kwargs["request"] == update
    assert captured_kwargs["updated_by"] == "system_user"
    assert result == fake_metric


def test_delete_ticket_metrics_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    metrics_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(ticket_metrics_service, "delete_ticket_metrics", fake_delete)

    result = delete_ticket_metrics_admin_endpoint(
        ticket_id=ticket_id,
        metrics_id=metrics_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="del_user",
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["metrics_id"] == metrics_id
    assert result is None


def test_list_ticket_status_durations_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_durations: List[TicketStatusDurationOut] = [
        _fake_status_duration_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            duration_id=uuid.uuid4(),
            status="pending",
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_durations, total

    monkeypatch.setattr(
        ticket_status_duration_service, "list_ticket_status_durations", fake_list
    )

    result = list_ticket_status_durations_admin_endpoint(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        status=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_durations


def test_create_ticket_status_duration_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = AdminCreateTicketStatusDuration(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status="open",
        started_at=None,
        ended_at=None,
        duration_seconds=None,
    )
    fake_duration = _fake_status_duration_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        duration_id=uuid.uuid4(),
        status=payload.status,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_duration

    monkeypatch.setattr(
        ticket_status_duration_service,
        "create_ticket_status_duration",
        fake_create,
    )

    result = create_ticket_status_duration_admin_endpoint(
        ticket_id=ticket_id,
        duration_in=payload,
        db=fake_db,
        x_user="admin_user",
    )

    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "admin_user"
    assert result == fake_duration


def test_update_ticket_status_duration_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    duration_id = uuid.uuid4()
    fake_db = DummySession()
    update = AdminUpdateTicketStatusDuration(status="on_hold")
    fake_duration = _fake_status_duration_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        duration_id=duration_id,
        status=update.status,
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_duration

    monkeypatch.setattr(
        ticket_status_duration_service,
        "update_ticket_status_duration",
        fake_update,
    )

    result = update_ticket_status_duration_admin_endpoint(
        ticket_id=ticket_id,
        duration_id=duration_id,
        duration_update=update,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="sys_user",
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["duration_id"] == duration_id
    assert captured_kwargs["request"] == update
    assert captured_kwargs["updated_by"] == "sys_user"
    assert result == fake_duration


def test_delete_ticket_status_duration_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    ticket_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    duration_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(
        ticket_status_duration_service,
        "delete_ticket_status_duration",
        fake_delete,
    )

    result = delete_ticket_status_duration_admin_endpoint(
        ticket_id=ticket_id,
        duration_id=duration_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="del_user",
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["duration_id"] == duration_id
    assert result is None