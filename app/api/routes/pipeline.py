"""FastAPI router for Pipeline endpoints.

Provides CRUD operations for pipelines.  Pipelines are scoped by tenant
and identified by UUID.  Use this router to manage pipeline entities.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import pipeline_service


router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("/", response_model=List[schemas.PipelineRead])
def list_pipelines(
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.PipelineRead]:
    return pipeline_service.list_pipelines(db, tenant_id)


@router.post("/", response_model=schemas.PipelineRead, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    pipeline_in: schemas.PipelineCreate,
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    pipeline = pipeline_service.create_pipeline(db, tenant_id, user_id, pipeline_in)
    return pipeline


@router.get("/{pipeline_id}", response_model=schemas.PipelineRead)
def get_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline ID"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    pipeline = pipeline_service.get_pipeline(db, pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


@router.patch("/{pipeline_id}", response_model=schemas.PipelineRead)
def update_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    pipeline_id: UUID = Path(..., description="Pipeline ID"),
    pipeline_in: schemas.PipelineUpdate,
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    pipeline = pipeline_service.get_pipeline(db, pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    updated = pipeline_service.update_pipeline(db, pipeline, user_id, pipeline_in)
    return updated


@router.delete(
    "/{pipeline_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline ID"),
    db: Session = Depends(get_db),
) -> Response:
    pipeline = pipeline_service.get_pipeline(db, pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    pipeline_service.delete_pipeline(db, pipeline)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)