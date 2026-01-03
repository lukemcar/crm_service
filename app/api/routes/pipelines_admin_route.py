"""
FastAPI router for Pipeline admin endpoints.

Admin routes provide CRUD operations for pipelines across tenants.  The
collection endpoint is exposed at ``/admin/pipelines`` and supports
optional filtering by name as well as pagination.  Mutating endpoints
require an explicit ``tenant_id`` query parameter to ensure that
pipelines are always created, updated or deleted within a known
tenant context.

All mutating operations accept an ``X‑User`` header which is passed
through to the service layer to populate audit fields.  Business logic
is delegated to ``pipeline_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import pipeline_service


router = APIRouter(prefix="/admin/pipelines", tags=["pipelines"])


@router.get("/", response_model=schemas.PaginationEnvelope[schemas.PipelineRead])
def list_pipelines(
    *,
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier for scoping; omit to list all tenants"
    ),
    name: Optional[str] = Query(
        None, description="Filter pipelines by name (case‑insensitive substring match)"
    ),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of pipelines to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of pipelines to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.PipelineRead]:
    """List pipelines (admin context).

    Allows optional filtering by tenant and name, and supports pagination.
    """
    items, total = pipeline_service.service_list_pipelines(
        db,
        tenant_id=tenant_id,
        name=name,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[schemas.PipelineRead](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=schemas.PipelineRead, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier for the new pipeline"),
    pipeline_in: schemas.PipelineCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    """Create a pipeline (admin context).

    The ``tenant_id`` query parameter is required to specify the owner
    tenant.  The ``X-User`` header populates audit fields.
    """
    pipeline = pipeline_service.service_create_pipeline(
        db,
        tenant_id=tenant_id,
        pipeline_in=pipeline_in,
        created_user=x_user,
    )
    return pipeline


@router.get("/{pipeline_id}", response_model=schemas.PipelineRead)
def get_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier for scoping"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    """Retrieve a pipeline by ID (admin context)."""
    pipeline = pipeline_service.service_get_pipeline(
        db,
        pipeline_id=pipeline_id,
        tenant_id=tenant_id,
    )
    return pipeline


@router.patch("/{pipeline_id}", response_model=schemas.PipelineRead)
def update_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier for the pipeline"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    pipeline_in: schemas.PipelineUpdate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    """Update a pipeline (admin context)."""
    updated = pipeline_service.service_update_pipeline(
        db,
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        pipeline_in=pipeline_in,
        updated_user=x_user,
    )
    return updated


@router.delete(
    "/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_pipeline(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier for the pipeline"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a pipeline (admin context)."""
    pipeline_service.service_delete_pipeline(
        db,
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)