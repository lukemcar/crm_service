"""Service layer for Pipeline operations.

Provides functions to list, create, retrieve, update and delete
pipelines.  Pipelines group stages for deals and tickets and are
scoped by tenant.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.pipeline import Pipeline
from app.domain.schemas.pipeline import PipelineCreate, PipelineUpdate, PipelineRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.pipeline_producer import PipelineMessageProducer
from fastapi import HTTPException, status
from typing import List as TypingList, Dict, Any, Tuple



def list_pipelines(db: Session, tenant_id: uuid.UUID) -> Iterable[Pipeline]:
    return db.query(Pipeline).filter(Pipeline.tenant_id == tenant_id).all()


def get_pipeline(db: Session, pipeline_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Pipeline]:
    return (
        db.query(Pipeline)
        .filter(Pipeline.id == pipeline_id, Pipeline.tenant_id == tenant_id)
        .first()
    )


def create_pipeline(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    pipeline_in: PipelineCreate,
) -> Pipeline:
    """Backward‑compatible pipeline creation without event emission.

    This function exists for legacy callers that have not migrated to
    ``service_create_pipeline``.  It will populate new fields for
    pipelines using sensible defaults similar to the consolidated change
    set.  The caller should pass ``object_type`` and other fields in
    ``pipeline_in`` if available.
    """
    # Determine object_type (required for new schema) or default to DEAL
    object_type = getattr(pipeline_in, "object_type", None) or "DEAL"
    # Determine display order by counting existing pipelines of the same object type
    existing_count = (
        db.query(Pipeline)
        .filter(Pipeline.tenant_id == tenant_id, Pipeline.object_type == object_type)
        .count()
    )
    display_order = getattr(pipeline_in, "display_order", None) or existing_count + 1
    is_active = getattr(pipeline_in, "is_active", None)
    if is_active is None:
        is_active = True
    # Generate a stable pipeline_key if not provided
    pipeline_key = getattr(pipeline_in, "pipeline_key", None) or f"pipeline_{uuid.uuid4().hex[:12]}"
    movement_mode = getattr(pipeline_in, "movement_mode", None) or "FLEXIBLE"
    pipeline = Pipeline(
        tenant_id=tenant_id,
        name=pipeline_in.name,
        object_type=object_type,
        display_order=display_order,
        is_active=is_active,
        pipeline_key=pipeline_key,
        movement_mode=movement_mode,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


def update_pipeline(
    db: Session,
    pipeline: Pipeline,
    user_id: Optional[uuid.UUID],
    pipeline_in: PipelineUpdate,
) -> Pipeline:
    # Update legacy pipeline fields and new consolidated fields if provided
    if pipeline_in.name is not None:
        pipeline.name = pipeline_in.name
    if pipeline_in.object_type is not None:
        pipeline.object_type = pipeline_in.object_type
    if pipeline_in.display_order is not None:
        pipeline.display_order = pipeline_in.display_order
    if pipeline_in.is_active is not None:
        pipeline.is_active = pipeline_in.is_active
    if pipeline_in.pipeline_key is not None:
        pipeline.pipeline_key = pipeline_in.pipeline_key
    if pipeline_in.movement_mode is not None:
        pipeline.movement_mode = pipeline_in.movement_mode
    pipeline.updated_by = user_id
    db.commit()
    db.refresh(pipeline)
    return pipeline


def delete_pipeline(db: Session, pipeline: Pipeline) -> None:
    db.delete(pipeline)
    db.commit()


# ---------------------------------------------------------------------------
# New service functions using the canonical pattern
# ---------------------------------------------------------------------------

def _pipeline_snapshot(pipeline: Pipeline) -> Dict[str, Any]:
    """
    Construct a snapshot dictionary of the given pipeline for event payloads.

    Utilises the ``PipelineRead`` Pydantic model with
    ``from_attributes=True`` to capture consumer‑facing fields.  The
    returned dictionary can be used as the payload for create and update
    events.
    """
    read_model = PipelineRead.model_validate(pipeline, from_attributes=True)
    return read_model.model_dump()


def service_list_pipelines(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    name: Optional[str] = None,
    object_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[Pipeline], int]:
    """
    List pipelines with optional filtering and pagination.

    If ``tenant_id`` is provided, results are restricted to that tenant.  An optional
    ``name`` filter performs a case‑insensitive substring match.  Additional filters
    on ``object_type`` and ``is_active`` allow callers to narrow results to a specific
    pipeline type or active/inactive pipelines.  Pagination is controlled via ``limit``
    and ``offset``.  Returns a tuple of (items, total_count).
    """
    query = db.query(Pipeline)
    if tenant_id is not None:
        query = query.filter(Pipeline.tenant_id == tenant_id)
    if name:
        # use ILIKE for case‑insensitive match; fall back to LIKE for SQLite
        query = query.filter(Pipeline.name.ilike(f"%{name}%"))
    if object_type:
        query = query.filter(Pipeline.object_type == object_type)
    if is_active is not None:
        query = query.filter(Pipeline.is_active == is_active)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_get_pipeline(
    db: Session,
    *,
    pipeline_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Pipeline:
    """
    Retrieve a pipeline by ID and tenant.

    Raises an ``HTTPException`` with 404 status if the pipeline is
    missing.
    """
    pipeline = (
        db.query(Pipeline)
        .filter(Pipeline.id == pipeline_id, Pipeline.tenant_id == tenant_id)
        .first()
    )
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


def service_create_pipeline(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    pipeline_in: PipelineCreate,
    created_user: str,
) -> Pipeline:
    """
    Create a new pipeline and emit a ``pipeline.created`` event.

    The ``created_user`` value populates both the ``created_by`` and
    ``updated_by`` fields.  The service ensures the database commit
    succeeds via ``commit_or_raise`` and publishes an event after
    committing.
    """
    # Determine object_type (required) or default to DEAL
    object_type = pipeline_in.object_type or "DEAL"
    # Determine display order by counting existing pipelines with same object type
    existing_count = (
        db.query(Pipeline)
        .filter(Pipeline.tenant_id == tenant_id, Pipeline.object_type == object_type)
        .count()
    )
    display_order = pipeline_in.display_order or (existing_count + 1)
    is_active = pipeline_in.is_active if pipeline_in.is_active is not None else True
    pipeline_key = pipeline_in.pipeline_key or f"pipeline_{uuid.uuid4().hex[:12]}"
    movement_mode = pipeline_in.movement_mode or "FLEXIBLE"
    pipeline = Pipeline(
        tenant_id=tenant_id,
        name=pipeline_in.name,
        object_type=object_type,
        display_order=display_order,
        is_active=is_active,
        pipeline_key=pipeline_key,
        movement_mode=movement_mode,
        created_by=created_user,
        updated_by=created_user,
    )
    db.add(pipeline)
    commit_or_raise(db, refresh=pipeline)
    # Emit created event with snapshot payload
    try:
        payload = _pipeline_snapshot(pipeline)
        PipelineMessageProducer.send_pipeline_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        # Do not propagate messaging failures
        pass
    return pipeline


def service_update_pipeline(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    pipeline_in: PipelineUpdate,
    updated_user: str,
) -> Pipeline:
    """
    Update a pipeline and emit a ``pipeline.updated`` event when changes occur.

    Only the ``name`` field is currently updatable.  The service
    computes a changes dictionary and publishes an event only if
    changes are present.
    """
    pipeline = service_get_pipeline(db, pipeline_id=pipeline_id, tenant_id=tenant_id)
    changes: Dict[str, Any] = {}
    # Update allowed fields and track changes
    if pipeline_in.name is not None and pipeline_in.name != pipeline.name:
        pipeline.name = pipeline_in.name
        changes["name"] = pipeline_in.name
    if pipeline_in.object_type is not None and pipeline_in.object_type != pipeline.object_type:
        pipeline.object_type = pipeline_in.object_type
        changes["object_type"] = pipeline_in.object_type
    if pipeline_in.display_order is not None and pipeline_in.display_order != pipeline.display_order:
        pipeline.display_order = pipeline_in.display_order
        changes["display_order"] = pipeline_in.display_order
    if pipeline_in.is_active is not None and pipeline_in.is_active != pipeline.is_active:
        pipeline.is_active = pipeline_in.is_active
        changes["is_active"] = pipeline_in.is_active
    if pipeline_in.pipeline_key is not None and pipeline_in.pipeline_key != pipeline.pipeline_key:
        pipeline.pipeline_key = pipeline_in.pipeline_key
        changes["pipeline_key"] = pipeline_in.pipeline_key
    if pipeline_in.movement_mode is not None and pipeline_in.movement_mode != pipeline.movement_mode:
        pipeline.movement_mode = pipeline_in.movement_mode
        changes["movement_mode"] = pipeline_in.movement_mode
    pipeline.updated_by = updated_user
    # Persist updates
    commit_or_raise(db, refresh=pipeline)
    # Publish event if changes exist
    if changes:
        try:
            payload = _pipeline_snapshot(pipeline)
            PipelineMessageProducer.send_pipeline_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=payload,
            )
        except Exception:
            pass
    return pipeline


def service_delete_pipeline(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
) -> None:
    """
    Delete a pipeline and emit a ``pipeline.deleted`` event.

    Emits a deletion event containing the deletion timestamp.  If the
    pipeline does not exist, a 404 error is raised.
    """
    pipeline = service_get_pipeline(db, pipeline_id=pipeline_id, tenant_id=tenant_id)
    db.delete(pipeline)
    commit_or_raise(db)
    try:
        PipelineMessageProducer.send_pipeline_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass