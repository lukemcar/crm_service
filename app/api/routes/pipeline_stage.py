"""FastAPI router for PipelineStage endpoints.

Defines endpoints for listing, creating, updating and deleting pipeline
stages.  Stages are nested under pipelines for listing and creation,
but individual stage retrieval, update and deletion are performed via
stage ID.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import pipeline_stage_service
from app.domain.services import pipeline_service


router = APIRouter(prefix="/pipelines", tags=["pipeline stages"])


@router.get("/{pipeline_id}/stages", response_model=List[schemas.PipelineStageRead])
def list_stages(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline ID"),
    db: Session = Depends(get_db),
) -> List[schemas.PipelineStageRead]:
    # Ensure pipeline exists within tenant
    pipeline = pipeline_service.get_pipeline(db, pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline_stage_service.list_stages(db, pipeline_id)


@router.post("/{pipeline_id}/stages", response_model=schemas.PipelineStageRead, status_code=status.HTTP_201_CREATED)
def create_stage(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    pipeline_id: UUID = Path(..., description="Pipeline ID"),
    stage_in: schemas.PipelineStageCreate,
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    # Validate pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    # Use provided pipeline_id even if stage_in specifies another; enforce path param
    stage_in_data = stage_in.copy(update={"pipeline_id": pipeline_id})
    stage = pipeline_stage_service.create_stage(db, user_id, stage_in_data)
    return stage


@router.get("/stages/{stage_id}", response_model=schemas.PipelineStageRead)
def get_stage(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    stage_id: UUID = Path(..., description="Stage ID"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    stage = pipeline_stage_service.get_stage(db, stage_id)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    # Optionally verify tenant by checking pipeline
    pipeline = pipeline_service.get_pipeline(db, stage.pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found for tenant")
    return stage


@router.patch("/stages/{stage_id}", response_model=schemas.PipelineStageRead)
def update_stage(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    stage_id: UUID = Path(..., description="Stage ID"),
    stage_in: schemas.PipelineStageUpdate,
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    stage = pipeline_stage_service.get_stage(db, stage_id)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    # Validate pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, stage.pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found for tenant")
    updated = pipeline_stage_service.update_stage(db, stage, user_id, stage_in)
    return updated


@router.delete(
    "/stages/{stage_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_stage(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    stage_id: UUID = Path(..., description="Stage ID"),
    db: Session = Depends(get_db),
) -> Response:
    stage = pipeline_stage_service.get_stage(db, stage_id)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    # Validate pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, stage.pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found for tenant")
    pipeline_stage_service.delete_stage(db, stage)
    return Response(status_code=status.HTTP_204_NO_CONTENT)