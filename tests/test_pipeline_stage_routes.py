"""Tests for the Pipeline Stage admin and tenant routes.

These tests verify that the refactored pipeline stage endpoints
correctly delegate to the service layer and derive tenant IDs
appropriately.  Stubs are used for database queries and service
functions to avoid requiring a real database.  Both admin and tenant
contexts are covered, including listing, creation, retrieval,
update and deletion of stages.  Audit fields from the ``X‑User``
header are propagated to the service layer on mutating requests.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.pipeline_stage import (
    PipelineStageCreate,
    PipelineStageUpdate,
    PipelineStageRead,
)
import app.domain.services.pipeline_service as pipeline_service
import app.domain.services.pipeline_stage_service as stage_service

from app.api.routes.pipeline_stages_admin_route import (
    list_stages as list_stages_admin,
    create_stage as create_stage_admin,
    get_stage as get_stage_admin,
    update_stage as update_stage_admin,
    delete_stage as delete_stage_admin,
)
from app.api.routes.pipeline_stages_tenant_route import (
    list_stages as list_stages_tenant,
    create_stage as create_stage_tenant,
    get_stage as get_stage_tenant,
    update_stage as update_stage_tenant,
    delete_stage as delete_stage_tenant,
)


class DummySession(Session):
    """Stand‑in for SQLAlchemy Session used in test stubs."""

    def __init__(self, pipeline_tenant_id: uuid.UUID | None = None) -> None:
        super().__init__()
        self._pipeline_tenant_id = pipeline_tenant_id

    # Provide a ``query`` method that returns a dummy query object when
    # listing stages in the admin context.  The dummy query's ``filter``
    # returns self, and ``first`` returns a pipeline-like object with
    # tenant_id equal to the configured tenant ID.  If no tenant ID is
    # configured, ``first`` returns None to simulate a missing pipeline.
    class _DummyQuery:
        def __init__(self, tenant_id: uuid.UUID | None) -> None:
            self._tenant_id = tenant_id

        def filter(self, *args, **kwargs):  # noqa: D401
            """Return self to allow chained calls."""
            return self

        def first(self):  # noqa: D401
            """Return a dummy pipeline-like object or None."""
            if self._tenant_id is None:
                return None
            return type("DummyPipeline", (object,), {"tenant_id": self._tenant_id})()

    def query(self, *args, **kwargs):  # noqa: D401
        """Return a dummy query for Pipeline lookup in admin stage routes."""
        return self._DummyQuery(self._pipeline_tenant_id)


def _fake_stage_read(
    tenant_id: uuid.UUID,
    stage_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    name: str = "Stage",
    display_order: int = 1,
    probability: float | None = None,
    created_by: str = "tester",
    updated_by: str = "tester",
) -> PipelineStageRead:
    """Construct a ``PipelineStageRead`` with sensible defaults and dynamic timestamps."""
    now = datetime.now(timezone.utc)
    return PipelineStageRead(
        id=stage_id,
        pipeline_id=pipeline_id,
        name=name,
        display_order=display_order,
        probability=probability,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        updated_by=updated_by,
    )


# ---------------------------------------------------------------------------
# Admin list
# ---------------------------------------------------------------------------


def test_list_stages_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin list endpoint should derive tenant ID from the pipeline and forward pagination."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession(pipeline_tenant_id=tenant_id)
    fake_stages: List[PipelineStageRead] = [
        _fake_stage_read(tenant_id=tenant_id, stage_id=uuid.uuid4(), pipeline_id=pipeline_id)
    ]
    total = 1
    captured: dict = {}

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_stages, total

    monkeypatch.setattr(stage_service, "service_list_stages", fake_list)

    result = list_stages_admin(
        pipeline_id=pipeline_id,
        limit=5,
        offset=0,
        db=fake_db,
    )

    # The derived tenant ID is passed through to the service
    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["limit"] == 5
    assert captured["offset"] == 0
    assert captured["db"] is fake_db
    assert result.total == total
    assert len(result.items) == len(fake_stages)


# ---------------------------------------------------------------------------
# Admin create
# ---------------------------------------------------------------------------


def test_create_stage_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin create endpoint should derive tenant ID and forward audit info."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession(pipeline_tenant_id=tenant_id)
    payload = PipelineStageCreate(
        pipeline_id=pipeline_id,
        name="New Stage",
        display_order=1,
        probability=None,
    )
    fake_stage = _fake_stage_read(
        tenant_id=tenant_id, stage_id=uuid.uuid4(), pipeline_id=pipeline_id, name=payload.name
    )
    captured: dict = {}

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_stage

    monkeypatch.setattr(stage_service, "service_create_stage", fake_create)

    result = create_stage_admin(
        pipeline_id=pipeline_id,
        stage_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["stage_in"] == payload
    assert captured["created_user"] == "creator"
    assert captured["db"] is fake_db
    assert result.id == fake_stage.id


# ---------------------------------------------------------------------------
# Admin get
# ---------------------------------------------------------------------------


def test_get_stage_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin get endpoint should call the service to retrieve a stage by ID."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    fake_stage = _fake_stage_read(
        tenant_id=tenant_id, stage_id=stage_id, pipeline_id=pipeline_id
    )

    monkeypatch.setattr(
        stage_service, "service_get_stage", lambda db, stage_id: fake_stage
    )

    result = get_stage_admin(
        stage_id=stage_id,
        db=fake_db,
    )

    assert result.id == fake_stage.id


# ---------------------------------------------------------------------------
# Admin update
# ---------------------------------------------------------------------------


def test_update_stage_admin_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin update endpoint should derive tenant ID and forward audit info."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineStageUpdate(name="Updated Stage", display_order=2)
    fake_stage = _fake_stage_read(
        tenant_id=tenant_id, stage_id=stage_id, pipeline_id=pipeline_id, name=payload.name or "Stage"
    )
    captured: dict = {}

    # Return a stage with tenant_id so update can derive it
    monkeypatch.setattr(
        stage_service, "service_get_stage", lambda db, stage_id: type("DummyStage", (object,), {"id": stage_id, "tenant_id": tenant_id})()
    )

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_stage

    monkeypatch.setattr(stage_service, "service_update_stage", fake_update)

    result = update_stage_admin(
        stage_id=stage_id,
        stage_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["stage_id"] == stage_id
    assert captured["stage_in"] == payload
    assert captured["updated_user"] == "editor"
    assert captured["db"] is fake_db
    assert result.id == fake_stage.id


# ---------------------------------------------------------------------------
# Admin delete
# ---------------------------------------------------------------------------


def test_delete_stage_admin_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin delete endpoint should derive tenant ID and pass stage ID to the service layer."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    # Return a stage with tenant_id so delete can derive it
    monkeypatch.setattr(
        stage_service, "service_get_stage", lambda db, stage_id: type("DummyStage", (object,), {"id": stage_id, "tenant_id": tenant_id})()
    )

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(stage_service, "service_delete_stage", fake_delete)

    result = delete_stage_admin(
        stage_id=stage_id,
        db=fake_db,
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["stage_id"] == stage_id
    assert captured["db"] is fake_db
    assert result.status_code == 204


# ---------------------------------------------------------------------------
# Tenant list
# ---------------------------------------------------------------------------


def test_list_stages_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant list endpoint should validate pipeline ownership and forward pagination."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession()
    fake_stages: List[PipelineStageRead] = [
        _fake_stage_read(tenant_id=tenant_id, stage_id=uuid.uuid4(), pipeline_id=pipeline_id)
    ]
    total = 1
    captured: dict = {}

    # Stub pipeline_service.service_get_pipeline to return a dummy pipeline
    monkeypatch.setattr(
        pipeline_service,
        "service_get_pipeline",
        lambda db, pipeline_id, tenant_id: object(),
    )

    def fake_list(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_stages, total

    monkeypatch.setattr(stage_service, "service_list_stages", fake_list)

    result = list_stages_tenant(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["limit"] is None
    assert captured["offset"] is None
    assert captured["db"] is fake_db
    assert result.total == total
    assert len(result.items) == len(fake_stages)


# ---------------------------------------------------------------------------
# Tenant create
# ---------------------------------------------------------------------------


def test_create_stage_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant create endpoint should validate pipeline and forward audit info."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineStageCreate(
        pipeline_id=pipeline_id,
        name="Tenant Stage",
        display_order=1,
        probability=None,
    )
    fake_stage = _fake_stage_read(
        tenant_id=tenant_id, stage_id=uuid.uuid4(), pipeline_id=pipeline_id, name=payload.name
    )
    captured: dict = {}

    # Stub pipeline_service.service_get_pipeline to return a dummy pipeline
    monkeypatch.setattr(
        pipeline_service,
        "service_get_pipeline",
        lambda db, pipeline_id, tenant_id: object(),
    )

    def fake_create(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_stage

    monkeypatch.setattr(stage_service, "service_create_stage", fake_create)

    result = create_stage_tenant(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        stage_in=payload,
        db=fake_db,
        x_user="creator",
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["pipeline_id"] == pipeline_id
    assert captured["stage_in"] == payload
    assert captured["created_user"] == "creator"
    assert captured["db"] is fake_db
    assert result.id == fake_stage.id


# ---------------------------------------------------------------------------
# Tenant get
# ---------------------------------------------------------------------------


def test_get_stage_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant get endpoint should validate stage ownership and return the stage."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()

    class DummyStage:
        def __init__(self, id: uuid.UUID, pipeline_id: uuid.UUID, tenant_id: uuid.UUID):
            self.id = id
            self.pipeline_id = pipeline_id
            self.tenant_id = tenant_id

    dummy_stage = DummyStage(stage_id, pipeline_id, tenant_id)

    monkeypatch.setattr(
        stage_service,
        "service_get_stage",
        lambda db, stage_id: dummy_stage,
    )

    result = get_stage_tenant(
        tenant_id=tenant_id,
        stage_id=stage_id,
        db=fake_db,
    )

    assert result.id == dummy_stage.id


# ---------------------------------------------------------------------------
# Tenant update
# ---------------------------------------------------------------------------


def test_update_stage_tenant_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant update endpoint should validate stage ownership and forward audit info."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    payload = PipelineStageUpdate(name="Tenant Updated", display_order=2)
    fake_stage = _fake_stage_read(
        tenant_id=tenant_id,
        stage_id=stage_id,
        pipeline_id=pipeline_id,
        name=payload.name or "Stage",
    )
    captured: dict = {}

    class DummyStage:
        def __init__(self, id: uuid.UUID, pipeline_id: uuid.UUID, tenant_id: uuid.UUID):
            self.id = id
            self.pipeline_id = pipeline_id
            self.tenant_id = tenant_id

    dummy_stage = DummyStage(stage_id, pipeline_id, tenant_id)

    monkeypatch.setattr(
        stage_service,
        "service_get_stage",
        lambda db, stage_id: dummy_stage,
    )

    def fake_update(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return fake_stage

    monkeypatch.setattr(stage_service, "service_update_stage", fake_update)

    result = update_stage_tenant(
        tenant_id=tenant_id,
        stage_id=stage_id,
        stage_in=payload,
        db=fake_db,
        x_user="editor",
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["stage_id"] == stage_id
    assert captured["stage_in"] == payload
    assert captured["updated_user"] == "editor"
    assert captured["db"] is fake_db
    assert result.id == fake_stage.id


# ---------------------------------------------------------------------------
# Tenant delete
# ---------------------------------------------------------------------------


def test_delete_stage_tenant_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant delete endpoint should validate stage ownership and pass audit info."""
    tenant_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    stage_id = uuid.uuid4()
    fake_db = DummySession()
    captured: dict = {}

    class DummyStage:
        def __init__(self, id: uuid.UUID, pipeline_id: uuid.UUID, tenant_id: uuid.UUID):
            self.id = id
            self.pipeline_id = pipeline_id
            self.tenant_id = tenant_id

    dummy_stage = DummyStage(stage_id, pipeline_id, tenant_id)

    monkeypatch.setattr(
        stage_service,
        "service_get_stage",
        lambda db, stage_id: dummy_stage,
    )

    def fake_delete(db, **kwargs):
        captured["db"] = db
        captured.update(kwargs)
        return None

    monkeypatch.setattr(stage_service, "service_delete_stage", fake_delete)

    result = delete_stage_tenant(
        tenant_id=tenant_id,
        stage_id=stage_id,
        db=fake_db,
        x_user="deleter",
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["stage_id"] == stage_id
    assert captured["deleted_user"] == "deleter"
    assert captured["db"] is fake_db
    assert result.status_code == 204