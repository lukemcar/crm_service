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
from app.domain.schemas.pipeline import PipelineCreate, PipelineUpdate


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
    pipeline = Pipeline(
        tenant_id=tenant_id,
        name=pipeline_in.name,
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
    if pipeline_in.name is not None:
        pipeline.name = pipeline_in.name
    pipeline.updated_by = user_id
    db.commit()
    db.refresh(pipeline)
    return pipeline


def delete_pipeline(db: Session, pipeline: Pipeline) -> None:
    db.delete(pipeline)
    db.commit()