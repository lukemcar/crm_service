"""
FastAPI router for Pipeline Stage admin endpoints.

Admin routes expose collection and singleton endpoints for stages.  The
collection endpoints are nested under pipelines (``/admin/pipelines/{pipeline_id}/stages``)
while singleton endpoints live at ``/admin/stages/{stage_id}``.

Admin listing does not accept a tenant_id query parameter; the
pipeline's tenant is derived from the pipeline itself to enforce
consistent scoping.  Mutating operations use the derived tenant ID
for event emission.

All mutating endpoints accept an optional ``X‑User`` header which is
passed to the service layer to populate audit fields.

Business logic is delegated to ``pipeline_stage_service.py`` and
``pipeline_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.models.pipeline import Pipeline
from app.domain.services import pipeline_stage_service


# Parent router
router = APIRouter(tags=["pipeline stages"])

# ---------------------------------------------------------------------------
# Collection endpoints: /admin/pipelines/{pipeline_id}/stages
# ---------------------------------------------------------------------------

collection_router = APIRouter(prefix="/admin/pipelines/{pipeline_id}/stages")


@collection_router.get("/", response_model=schemas.PaginationEnvelope[schemas.PipelineStageRead])
def list_stages(
    *,
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of stages to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of stages to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.PipelineStageRead]:
    """List stages for a pipeline (admin context).

    Derives the tenant ID from the pipeline itself to scope the query.
    """
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    items, total = pipeline_stage_service.service_list_stages(
        db,
        tenant_id=pipeline.tenant_id,
        pipeline_id=pipeline_id,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[schemas.PipelineStageRead](
        items=items, total=total, limit=limit, offset=offset
    )


@collection_router.post("/", response_model=schemas.PipelineStageRead, status_code=status.HTTP_201_CREATED)
def create_stage(
    *,
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    stage_in: schemas.PipelineStageCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    """Create a stage under a pipeline (admin context).

    The tenant ID is derived from the pipeline.  The ``pipeline_id`` in
    the request body is ignored and overwritten with the path parameter.
    """
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    stage = pipeline_stage_service.service_create_stage(
        db,
        tenant_id=pipeline.tenant_id,
        pipeline_id=pipeline_id,
        stage_in=stage_in,
        created_user=x_user,
    )
    return stage


# ---------------------------------------------------------------------------
# Singleton endpoints: /admin/stages/{stage_id}
# ---------------------------------------------------------------------------

singleton_router = APIRouter(prefix="/admin/stages")


@singleton_router.get("/{stage_id}", response_model=schemas.PipelineStageRead)
def get_stage(
    *,
    stage_id: UUID = Path(..., description="Stage identifier"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    """Retrieve a stage by ID (admin context)."""
    stage = pipeline_stage_service.service_get_stage(db, stage_id=stage_id)
    return stage


@singleton_router.patch("/{stage_id}", response_model=schemas.PipelineStageRead)
def update_stage(
    *,
    stage_id: UUID = Path(..., description="Stage identifier"),
    stage_in: schemas.PipelineStageUpdate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    """Update a stage (admin context).

    The tenant ID is derived from the stage itself and passed to the
    service for validation and event emission.
    """
    stage = pipeline_stage_service.service_get_stage(db, stage_id=stage_id)
    updated = pipeline_stage_service.service_update_stage(
        db,
        tenant_id=stage.tenant_id,
        stage_id=stage_id,
        stage_in=stage_in,
        updated_user=x_user,
    )
    return updated


@singleton_router.delete(
    "/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_stage(
    *,
    stage_id: UUID = Path(..., description="Stage identifier"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a stage (admin context).

    The tenant ID is derived from the stage itself and passed to the
    service for validation and event emission.
    """
    stage = pipeline_stage_service.service_get_stage(db, stage_id=stage_id)
    pipeline_stage_service.service_delete_stage(
        db,
        tenant_id=stage.tenant_id,
        stage_id=stage_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


router.include_router(collection_router)
router.include_router(singleton_router)