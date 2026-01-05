"""Tests for the Pipeline admin and tenant routes.

These tests ensure that the refactored pipeline endpoints delegate
correctly to the service layer and that audit fields from the
``X‑User`` header are propagated.  A lightweight ``DummySession``
class is used in place of a real SQLAlchemy session, and service
functions are monkeypatched to capture their inputs and return
predictable results.  Tests cover listing, creation, update and
deletion for both admin and tenant contexts.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.pipeline import PipelineCreate, PipelineUpdate, PipelineRead
import app.domain.services.pipeline_service as pipeline_service

from app.api.routes.pipelines_admin_route import (
    list_pipelines as list_pipelines_admin,
    create_pipeline as create_pipeline_admin,
    update_pipeline as update_pipeline_admin,
    delete_pipeline as delete_pipeline_admin,
)
from app.api.routes.pipelines_tenant_route import (
    list_pipelines as list_pipelines_tenant,
    create_pipeline as create_pipeline_tenant,
    update_pipeline as update_pipeline_tenant,
    delete_pipeline as delete_pipeline_tenant,
)


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    pass


def _fake_pipeline_read(
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    name: str = "Test Pipeline",
    object_type: str = "deal",
    display_order: int = 1,
    is_active: bool = True,
    pipeline_key: str | None = None,
    movement_mode: str = "SEQUENTIAL",
    created_by: str = "tester",
    updated_by: str = "tester",
) -> PipelineRead:
    """Construct a ``PipelineRead`` with sensible defaults and dynamic timestamps.

    Includes new pipeline fields such as object_type, display_order, is_active,
    pipeline_key and movement_mode to satisfy the updated schema.
    """
    now = datetime.now(timezone.utc)
    # Generate a predictable pipeline key if not supplied
    key = pipeline_key or "test-key"
    return PipelineRead(
        id=pipeline_id,
        tenant_id=tenant_id,
        name=name,
        object_type=object_type,
        display_order=display_order,
        is_active=is_active,
        pipeline_key=key,
        movement_mode=movement_mode,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


# ---------------------------------------------------------------------------
# Admin list
# ---------------------------------------------------------------------------


def test_list_pipelines_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should forward filters and pagination to the service layer."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_pipelines: List[PipelineRead] = [
        _fake_pipeline_read(tenant_id=tenant_id, pipeline_id=uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_pipelines, total

    monkeypatch.setattr(pipeline_service, "service_list_pipelines", fake_list)

    result = list_pipelines_admin(
        tenant_id=tenant_id,
        name="Search",
        object_type=None,
        is_active=None,
        limit=5,
        offset=0,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["name"] == "Search"
    assert captured.get("object_type") is None
    assert captured.get("is_active") is None
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert result.total == total
    assert len(result.items) == len(fake_pipelines)


# ---------------------------------------------------------------------------
# Admin create
# ---------------------------------------------------------------------------


def test_create_pipeline_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should pass ``X‑User`` through to the service layer."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineCreate(name="Admin Pipeline", object_type="deal")
    fake_pipeline = _fake_pipeline_read(
        tenant_id=tenant_id, pipeline_id=uuid.uuid4(), name=payload.name
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_pipeline

    monkeypatch.setattr(pipeline_service, "service_create_pipeline", fake_create)

    result = create_pipeline_admin(
        tenant_id=tenant_id,
        pipeline_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_in"] == payload
    assert captured["created_user"] == "creator"
    assert result.id == fake_pipeline.id


# ---------------------------------------------------------------------------
# Admin update
# ---------------------------------------------------------------------------


def test_update_pipeline_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin update endpoint should forward the modified user and pipeline ID."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineUpdate(name="Updated Name")
    fake_pipeline = _fake_pipeline_read(
        tenant_id=tenant_id, pipeline_id=pipeline_id, name=payload.name or "Test"
    )
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_pipeline

    monkeypatch.setattr(pipeline_service, "service_update_pipeline", fake_update)

    result = update_pipeline_admin(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        pipeline_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["pipeline_in"] == payload
    assert captured["updated_user"] == "editor"
    assert result.id == fake_pipeline.id


# ---------------------------------------------------------------------------
# Admin delete
# ---------------------------------------------------------------------------


def test_delete_pipeline_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should pass pipeline and tenant IDs to the service layer."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(pipeline_service, "service_delete_pipeline", fake_delete)

    result = delete_pipeline_admin(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    # Delete returns a Response with status 204
    assert result.status_code == 204


# ---------------------------------------------------------------------------
# Tenant list
# ---------------------------------------------------------------------------


def test_list_pipelines_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant list endpoint should forward optional filters and pagination."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_pipelines: List[PipelineRead] = [
        _fake_pipeline_read(tenant_id=tenant_id, pipeline_id=uuid.uuid4())
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_pipelines, total

    monkeypatch.setattr(pipeline_service, "service_list_pipelines", fake_list)

    result = list_pipelines_tenant(
        tenant_id=tenant_id,
        name=None,
        object_type=None,
        is_active=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured.get("name") is None
    assert captured.get("object_type") is None
    assert captured.get("is_active") is None
    assert captured.get("limit") is None
    assert captured.get("offset") is None
    assert result.total == total
    assert len(result.items) == len(fake_pipelines)


# ---------------------------------------------------------------------------
# Tenant create
# ---------------------------------------------------------------------------


def test_create_pipeline_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant create endpoint should pass through ``X‑User`` to the service layer."""
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineCreate(name="Tenant Pipeline", object_type="deal")
    fake_pipeline = _fake_pipeline_read(
        tenant_id=tenant_id, pipeline_id=uuid.uuid4(), name=payload.name
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_pipeline

    monkeypatch.setattr(pipeline_service, "service_create_pipeline", fake_create)

    result = create_pipeline_tenant(
        tenant_id=tenant_id,
        pipeline_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_in"] == payload
    assert captured["created_user"] == "creator"
    assert result.id == fake_pipeline.id


# ---------------------------------------------------------------------------
# Tenant update
# ---------------------------------------------------------------------------


def test_update_pipeline_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant update endpoint should forward the modified user and pipeline ID."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineUpdate(name="Tenant Updated")
    fake_pipeline = _fake_pipeline_read(
        tenant_id=tenant_id, pipeline_id=pipeline_id, name=payload.name or "Test"
    )
    captured: dict = {}

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_pipeline

    monkeypatch.setattr(pipeline_service, "service_update_pipeline", fake_update)

    result = update_pipeline_tenant(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        pipeline_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["pipeline_in"] == payload
    assert captured["updated_user"] == "editor"
    assert result.id == fake_pipeline.id


# ---------------------------------------------------------------------------
# Tenant delete
# ---------------------------------------------------------------------------


def test_delete_pipeline_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant delete endpoint should pass pipeline ID to the service layer."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(pipeline_service, "service_delete_pipeline", fake_delete)

    result = delete_pipeline_tenant(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        db=fake_db,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert result.status_code == 204