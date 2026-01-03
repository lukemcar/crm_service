"""
FastAPI router for Pipeline Stage tenant endpoints.

Tenant routes expose collection and singleton endpoints for stages
scoped by the tenant via the URL path.  Collection endpoints are
nested under pipelines (``/tenants/{tenant_id}/pipelines/{pipeline_id}/stages``)
while singleton endpoints live at ``/tenants/{tenant_id}/stages/{stage_id}``.

All mutating endpoints accept an ``X‑User`` header to capture audit
information.  Business logic is delegated to
``pipeline_stage_service.py`` and ``pipeline_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import pipeline_stage_service, pipeline_service


# Parent router
router = APIRouter(tags=["pipeline stages"])

# ---------------------------------------------------------------------------
# Collection endpoints: /tenants/{tenant_id}/pipelines/{pipeline_id}/stages
# ---------------------------------------------------------------------------

collection_router = APIRouter(prefix="/tenants/{tenant_id}/pipelines/{pipeline_id}/stages")


@collection_router.get("/", response_model=schemas.PaginationEnvelope[schemas.PipelineStageRead])
def list_stages(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of stages to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of stages to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.PipelineStageRead]:
    """List stages for a pipeline (tenant context).

    Validates that the pipeline belongs to the tenant before listing.
    """
    # Ensure pipeline exists within tenant
    pipeline_service.service_get_pipeline(
        db,
        pipeline_id=pipeline_id,
        tenant_id=tenant_id,
    )
    items, total = pipeline_stage_service.service_list_stages(
        db,
        tenant_id=tenant_id,
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    stage_in: schemas.PipelineStageCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    """Create a stage under a pipeline (tenant context).

    Validates that the pipeline belongs to the tenant.  The
    ``pipeline_id`` in the request body is ignored and overwritten with
    the path parameter.
    """
    pipeline_service.service_get_pipeline(
        db,
        pipeline_id=pipeline_id,
        tenant_id=tenant_id,
    )
    stage = pipeline_stage_service.service_create_stage(
        db,
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        stage_in=stage_in,
        created_user=x_user,
    )
    return stage


# ---------------------------------------------------------------------------
# Singleton endpoints: /tenants/{tenant_id}/stages/{stage_id}
# ---------------------------------------------------------------------------

singleton_router = APIRouter(prefix="/tenants/{tenant_id}/stages")


@singleton_router.get("/{stage_id}", response_model=schemas.PipelineStageRead)
def get_stage(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    stage_id: UUID = Path(..., description="Stage identifier"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    """Retrieve a stage by ID (tenant context).

    Ensures the stage belongs to the tenant.
    """
    stage = pipeline_stage_service.service_get_stage(db, stage_id=stage_id)
    if stage.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    return stage


@singleton_router.patch("/{stage_id}", response_model=schemas.PipelineStageRead)
def update_stage(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    stage_id: UUID = Path(..., description="Stage identifier"),
    stage_in: schemas.PipelineStageUpdate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineStageRead:
    """Update a stage (tenant context).

    Ensures the stage belongs to the tenant before updating.
    """
    stage = pipeline_stage_service.service_get_stage(db, stage_id=stage_id)
    if stage.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    updated = pipeline_stage_service.service_update_stage(
        db,
        tenant_id=tenant_id,
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    stage_id: UUID = Path(..., description="Stage identifier"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a stage (tenant context).

    Ensures the stage belongs to the tenant before deletion.
    """
    stage = pipeline_stage_service.service_get_stage(db, stage_id=stage_id)
    if stage.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    pipeline_stage_service.service_delete_stage(
        db,
        tenant_id=tenant_id,
        stage_id=stage_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Include sub‑routers
router.include_router(collection_router)
router.include_router(singleton_router)