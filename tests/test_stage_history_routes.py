"""
Tests for the Stage History tenant route.

These tests validate that the new stage history endpoint calls the
appropriate service function with the correct parameters and wraps the
results in a ``PaginationEnvelope``.  A ``DummySession`` class stands in
for a real SQLAlchemy session.  Only the list endpoint is currently
exposed for stage history.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.stage_history import StageHistoryRead
import app.domain.services.stage_history_service as history_service

from app.api.routes.stage_history_tenant_route import list_stage_history


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    pass


def _fake_history_read(
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    from_stage_id: uuid.UUID | None = None,
    to_stage_id: uuid.UUID | None = None,
) -> StageHistoryRead:
    """Construct a ``StageHistoryRead`` with sensible defaults."""
    now = datetime.now(timezone.utc)
    return StageHistoryRead(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        pipeline_id=None,
        from_stage_id=from_stage_id,
        to_stage_id=to_stage_id,
        changed_at=now,
        changed_by_user_id=None,
        source=None,
    )


def test_list_stage_history_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stage history list endpoint should pass parameters to the service."""
    tenant_id = uuid.uuid4()
    entity_type = "deal"
    entity_id = uuid.uuid4()
    fake_db = DummySession()
    fake_history: List[StageHistoryRead] = [
        _fake_history_read(tenant_id, entity_type, entity_id)
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, *, tenant_id, entity_type, entity_id, limit, offset):
        captured["db"] = db
        captured["tenant_id"] = tenant_id
        captured["entity_type"] = entity_type
        captured["entity_id"] = entity_id
        captured["limit"] = limit
        captured["offset"] = offset
        return fake_history, total

    monkeypatch.setattr(
        history_service,
        "list_stage_history_by_entity",
        fake_list,
    )

    result = list_stage_history(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["entity_type"] == entity_type
    assert captured["entity_id"] == entity_id
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_history)