"""Service layer for PipelineStage operations.

Manages CRUD operations for pipeline stages.  Stages belong to a
pipeline and define the progression of deals or tickets.  All
operations are scoped by the pipeline's tenant.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from fastapi import HTTPException, status

from app.domain.models.pipeline_stage import PipelineStage
from app.domain.schemas.pipeline_stage import (
    PipelineStageCreate,
    PipelineStageUpdate,
    PipelineStageRead,
)
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.pipeline_stage_producer import PipelineStageMessageProducer
from app.domain.models.pipeline import Pipeline
from typing import List as TypingList, Dict, Any, Tuple


def list_stages(db: Session, tenant_id: uuid.UUID , pipeline_id: uuid.UUID) -> Iterable[PipelineStage]:
    return (
        db.query(PipelineStage)
        .filter(PipelineStage.pipeline_id == pipeline_id, PipelineStage.tenant_id == tenant_id)
        .order_by(PipelineStage.stage_order.asc())
        .all()
    )


def get_stage(db: Session, stage_id: uuid.UUID) -> Optional[PipelineStage]:
    return db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()


def create_stage(
    db: Session,
    tentant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    stage_in: PipelineStageCreate,
) -> PipelineStage:
    # Legacy implementation retained for backward compatibility (will be removed)
    # pragma: no cover
    # This function uses tentant_id instead of tenant_id; new implementations
    # should call service_create_stage instead.
    # check to see if a stage with the same name exists in the same pipeline
    pipline = (
        db.query(PipelineStage)
        .filter(PipelineStage.pipeline_id == stage_in.pipeline_id)
        .first()
    )
    if not pipline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found.",
        )
    exiting_stage = (
        db.query(PipelineStage)
        .filter(
            PipelineStage.pipeline_id == stage_in.pipeline_id,
            or_(
                PipelineStage.name == stage_in.name,
                PipelineStage.stage_order == stage_in.stage_order,
            ),
        )
        .first()
    )
    if exiting_stage:
        if exiting_stage.name == stage_in.name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A stage with this name already exists in the pipeline.",
            )
        elif exiting_stage.stage_order == stage_in.stage_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A stage with this order already exists in the pipeline.",
            )   
    stage = PipelineStage(
        pipeline_id=stage_in.pipeline_id,
        name=stage_in.name,
        stage_order=stage_in.stage_order,
        probability=stage_in.probability,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage


def update_stage(
    db: Session,
    stage: PipelineStage,
    user_id: Optional[uuid.UUID],
    stage_in: PipelineStageUpdate,
) -> PipelineStage:
    # Legacy implementation retained for backward compatibility
    # pragma: no cover
    if stage_in.pipeline_id is not None:
        stage.pipeline_id = stage_in.pipeline_id
    if stage_in.name is not None:
        stage.name = stage_in.name
    if stage_in.stage_order is not None:
        stage.stage_order = stage_in.stage_order
    if stage_in.probability is not None:
        stage.probability = stage_in.probability
    stage.updated_by = user_id
    db.commit()
    db.refresh(stage)
    return stage


def delete_stage(db: Session, stage: PipelineStage) -> None:
    # Legacy implementation retained for backward compatibility
    # pragma: no cover
    db.delete(stage)
    db.commit()


# ---------------------------------------------------------------------------
# New service functions using the canonical pattern
# ---------------------------------------------------------------------------

def _stage_snapshot(stage: PipelineStage) -> Dict[str, Any]:
    """
    Create a snapshot dictionary of a stage for event payloads.

    Uses the ``PipelineStageRead`` Pydantic model with
    ``from_attributes=True`` to capture all consumer‑visible fields.  The
    returned dictionary can be used as the payload for created and
    updated events.
    """
    read_model = PipelineStageRead.model_validate(stage, from_attributes=True)
    return read_model.model_dump()


def service_list_stages(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[PipelineStage], int]:
    """
    List stages for a pipeline with optional pagination.

    Always filters by ``tenant_id`` and ``pipeline_id`` to enforce
    tenancy isolation.  Returns a tuple of (items, total_count).
    """
    query = (
        db.query(PipelineStage)
        .filter(
            PipelineStage.pipeline_id == pipeline_id,
            PipelineStage.tenant_id == tenant_id,
        )
        .order_by(PipelineStage.stage_order.asc())
    )
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_get_stage(
    db: Session,
    *,
    stage_id: uuid.UUID,
) -> PipelineStage:
    """
    Retrieve a pipeline stage by ID.

    Raises an ``HTTPException`` with 404 status if the stage is not found.
    """
    stage = db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    return stage


def service_create_stage(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    stage_in: PipelineStageCreate,
    created_user: str,
) -> PipelineStage:
    """
    Create a pipeline stage and emit a ``pipeline_stage.created`` event.

    Validates that the parent pipeline exists and belongs to the tenant,
    detects duplicate stage names or orders within the pipeline and
    publishes a creation event after committing.
    """
    # Validate pipeline existence and ownership
    pipeline = db.query(Pipeline).filter(
        Pipeline.id == pipeline_id,
        Pipeline.tenant_id == tenant_id,
    ).first()
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    # Check for duplicate name or order
    existing = db.query(PipelineStage).filter(
        PipelineStage.pipeline_id == pipeline_id,
        PipelineStage.tenant_id == tenant_id,
        or_(
            PipelineStage.name == stage_in.name,
            PipelineStage.stage_order == stage_in.stage_order,
        ),
    ).first()
    if existing:
        if existing.name == stage_in.name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A stage with this name already exists in the pipeline.",
            )
        elif existing.stage_order == stage_in.stage_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A stage with this order already exists in the pipeline.",
            )
    stage = PipelineStage(
        pipeline_id=pipeline_id,
        tenant_id=tenant_id,
        name=stage_in.name,
        stage_order=stage_in.stage_order,
        probability=stage_in.probability,
        created_by=created_user,
        updated_by=created_user,
    )
    db.add(stage)
    commit_or_raise(db, refresh=stage)
    # Emit creation event
    try:
        payload = _stage_snapshot(stage)
        PipelineStageMessageProducer.send_stage_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        pass
    return stage


def service_update_stage(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    stage_id: uuid.UUID,
    stage_in: PipelineStageUpdate,
    updated_user: str,
) -> PipelineStage:
    """
    Update a pipeline stage and emit a ``pipeline_stage.updated`` event when changes occur.

    Validates that the stage belongs to the tenant.  Optionally
    updates the name, order or probability.  If ``pipeline_id`` is
    provided, verifies the target pipeline exists and belongs to the
    tenant and checks for duplicates in the new pipeline.
    """
    stage = service_get_stage(db, stage_id=stage_id)
    if stage.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    changes: Dict[str, Any] = {}
    # Handle pipeline_id change
    if stage_in.pipeline_id is not None and stage_in.pipeline_id != stage.pipeline_id:
        # Validate new pipeline belongs to tenant
        new_pipeline = db.query(Pipeline).filter(
            Pipeline.id == stage_in.pipeline_id,
            Pipeline.tenant_id == tenant_id,
        ).first()
        if not new_pipeline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
        # Check for duplicate name or order in new pipeline
        duplicate = db.query(PipelineStage).filter(
            PipelineStage.pipeline_id == stage_in.pipeline_id,
            PipelineStage.tenant_id == tenant_id,
            or_(
                PipelineStage.name == (stage_in.name if stage_in.name is not None else stage.name),
                PipelineStage.stage_order == (stage_in.stage_order if stage_in.stage_order is not None else stage.stage_order),
            ),
        ).first()
        if duplicate:
            if duplicate.id != stage.id:
                # Only raise if duplicate refers to another record
                if duplicate.name == (stage_in.name if stage_in.name is not None else stage.name):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A stage with this name already exists in the target pipeline.",
                    )
                elif duplicate.stage_order == (stage_in.stage_order if stage_in.stage_order is not None else stage.stage_order):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A stage with this order already exists in the target pipeline.",
                    )
        stage.pipeline_id = stage_in.pipeline_id
        changes["pipeline_id"] = stage_in.pipeline_id
    # Update name
    if stage_in.name is not None and stage_in.name != stage.name:
        # Check for duplicate name in current pipeline (or new pipeline if changed)
        dup_name = db.query(PipelineStage).filter(
            PipelineStage.pipeline_id == stage.pipeline_id,
            PipelineStage.tenant_id == tenant_id,
            PipelineStage.name == stage_in.name,
            PipelineStage.id != stage.id,
        ).first()
        if dup_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A stage with this name already exists in the pipeline.",
            )
        stage.name = stage_in.name
        changes["name"] = stage_in.name
    # Update order
    if stage_in.stage_order is not None and stage_in.stage_order != stage.stage_order:
        dup_order = db.query(PipelineStage).filter(
            PipelineStage.pipeline_id == stage.pipeline_id,
            PipelineStage.tenant_id == tenant_id,
            PipelineStage.stage_order == stage_in.stage_order,
            PipelineStage.id != stage.id,
        ).first()
        if dup_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A stage with this order already exists in the pipeline.",
            )
        stage.stage_order = stage_in.stage_order
        changes["stage_order"] = stage_in.stage_order
    # Update probability
    if stage_in.probability is not None and stage_in.probability != stage.probability:
        stage.probability = stage_in.probability
        changes["probability"] = stage_in.probability
    stage.updated_by = updated_user
    commit_or_raise(db, refresh=stage)
    if changes:
        try:
            payload = _stage_snapshot(stage)
            PipelineStageMessageProducer.send_stage_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=payload,
            )
        except Exception:
            pass
    return stage


def service_delete_stage(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    stage_id: uuid.UUID,
) -> None:
    """
    Delete a pipeline stage and emit a ``pipeline_stage.deleted`` event.

    Validates that the stage belongs to the tenant before deleting.
    """
    stage = service_get_stage(db, stage_id=stage_id)
    if stage.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    db.delete(stage)
    commit_or_raise(db)
    try:
        PipelineStageMessageProducer.send_stage_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass