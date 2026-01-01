"""
Tests for ticket reporting primitives nested tenant routes.

This module verifies that the tenant endpoints for ticket metrics and
ticket status duration correctly delegate to the service layer and
return Pydantic objects constructed from service results.  Since
tenants have read‑only access to these resources, only list and get
operations are tested.
"""

from __future__ import annotations

import uuid
from typing import List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.ticket_metrics import TicketMetricsOut
from app.domain.schemas.ticket_status_duration import TicketStatusDurationOut
from app.domain.services import ticket_metrics_service, ticket_status_duration_service
from app.api.routes.tickets_tenant_nested_routes import (
    list_ticket_metrics_tenant_endpoint,
    get_ticket_metrics_tenant_endpoint,
    list_ticket_status_durations_tenant_endpoint,
    get_ticket_status_duration_tenant_endpoint,
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
    started_at: str | None = None,
    ended_at: str | None = None,
    duration_seconds: int | None = None,
) -> TicketStatusDurationOut:
    return TicketStatusDurationOut(
        id=duration_id,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        created_at=None,
        created_by="tester",
    )


def test_list_ticket_metrics_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_metrics: List[TicketMetricsOut] = [
        _fake_metrics_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            metrics_id=uuid.uuid4(),
            reply_count=3,
            reopen_count=1,
        )
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_metrics, total

    monkeypatch.setattr(ticket_metrics_service, "list_ticket_metrics", fake_list)

    result = list_ticket_metrics_tenant_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_metrics


def test_get_ticket_metrics_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    metrics_id = uuid.uuid4()
    fake_db = DummySession()
    fake_metric = _fake_metrics_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        metrics_id=metrics_id,
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_metric

    monkeypatch.setattr(ticket_metrics_service, "get_ticket_metrics", fake_get)

    result = get_ticket_metrics_tenant_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        metrics_id=metrics_id,
        db=fake_db,
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["metrics_id"] == metrics_id
    assert result == fake_metric


def test_list_ticket_status_durations_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    fake_db = DummySession()
    fake_durations: List[TicketStatusDurationOut] = [
        _fake_status_duration_out(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            duration_id=uuid.uuid4(),
            status="open",
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

    result = list_ticket_status_durations_tenant_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["ticket_id"] == ticket_id
    assert result == fake_durations


def test_get_ticket_status_duration_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    duration_id = uuid.uuid4()
    fake_db = DummySession()
    fake_duration = _fake_status_duration_out(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        duration_id=duration_id,
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_duration

    monkeypatch.setattr(
        ticket_status_duration_service, "get_ticket_status_duration", fake_get
    )

    result = get_ticket_status_duration_tenant_endpoint(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        duration_id=duration_id,
        db=fake_db,
    )

    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["duration_id"] == duration_id
    assert result == fake_duration