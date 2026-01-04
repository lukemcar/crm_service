"""
Tests for the StageHistory service functions.

These tests verify that the service layer correctly enforces tenant
matching when creating stage history entries and properly returns the
created object.  A lightweight ``DummySession`` class provides a
minimal SQLAlchemy session interface for adding and committing
instances without hitting a real database.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.models.stage_history import StageHistory
from app.domain.schemas.stage_history import StageHistoryCreate
import app.domain.services.stage_history_service as stage_history_service


class DummySession(Session):
    """Stand‑in for a SQLAlchemy Session used in test stubs."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[StageHistory] = []

    def query(self, model):  # type: ignore[override]
        # Return self to allow filter chaining; not needed for these tests
        return self

    def filter(self, *args, **kwargs):  # type: ignore[override]
        return self

    def count(self):  # type: ignore[override]
        return len(self.items)

    def all(self):  # type: ignore[override]
        return list(self.items)

    def add(self, instance):  # type: ignore[override]
        self.items.append(instance)

    def commit(self):  # type: ignore[override]
        pass

    def refresh(self, instance):  # type: ignore[override]
        pass


def test_service_create_stage_history_tenant_mismatch() -> None:
    """Creating a stage history with mismatched tenant IDs should raise a 400 HTTPException."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    history_in = StageHistoryCreate(
        tenant_id=other_tenant,
        entity_type="DEAL",
        entity_id=uuid.uuid4(),
        pipeline_id=None,
        from_stage_id=None,
        to_stage_id=None,
        changed_by_user_id=None,
        source="TEST",
    )
    with pytest.raises(HTTPException) as exc_info:
        stage_history_service.service_create_stage_history(
            db,
            tenant_id=tenant_id,
            history_in=history_in,
            changed_by_user_id=None,
        )
    assert exc_info.value.status_code == 400


def test_service_create_stage_history_success() -> None:
    """A valid create request should return a StageHistory instance with assigned fields."""
    db = DummySession()
    tenant_id = uuid.uuid4()
    history_in = StageHistoryCreate(
        tenant_id=tenant_id,
        entity_type="DEAL",
        entity_id=uuid.uuid4(),
        pipeline_id=None,
        from_stage_id=None,
        to_stage_id=None,
        changed_by_user_id=None,
        source="IMPORT",
    )
    result = stage_history_service.service_create_stage_history(
        db,
        tenant_id=tenant_id,
        history_in=history_in,
        changed_by_user_id=None,
    )
    # The result should be appended to db.items and have attributes set
    assert isinstance(result, StageHistory)
    assert result in db.items
    assert result.tenant_id == tenant_id
    assert result.entity_type == history_in.entity_type
    assert result.entity_id == history_in.entity_id
    # changed_at should be auto‑populated
    assert result.changed_at is not None