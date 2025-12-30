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
)


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
    db.delete(stage)
    db.commit()