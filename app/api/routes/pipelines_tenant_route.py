"""
FastAPI router for Pipeline tenant endpoints.

Tenant routes provide CRUD operations for pipelines scoped by the
tenant via the URL path.  The collection endpoint is
``/tenants/{tenant_id}/pipelines``.  All operations derive the tenant
identifier from the path and never accept a ``tenant_id`` query
parameter.  Mutating endpoints accept an ``X‑User`` header to
populate audit fields.

Business logic is delegated to ``pipeline_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import pipeline_service


router = APIRouter(prefix="/tenants/{tenant_id}/pipelines", tags=["pipelines"])


@router.get("/", response_model=schemas.PaginationEnvelope[schemas.PipelineRead])
def list_pipelines(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    name: Optional[str] = Query(
        None, description="Filter pipelines by name (case‑insensitive substring match)"
    ),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of pipelines to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of pipelines to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.PipelineRead]:
    """List pipelines for a tenant.

    Supports optional filtering by name and pagination.
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    pipeline_in: schemas.PipelineCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    """Create a pipeline for the tenant."""
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    """Retrieve a pipeline by ID (tenant context)."""
    pipeline = pipeline_service.service_get_pipeline(
        db,
        pipeline_id=pipeline_id,
        tenant_id=tenant_id,
    )
    return pipeline


@router.patch("/{pipeline_id}", response_model=schemas.PipelineRead)
def update_pipeline(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    pipeline_in: schemas.PipelineUpdate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.PipelineRead:
    """Update a pipeline (tenant context)."""
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    pipeline_id: UUID = Path(..., description="Pipeline identifier"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a pipeline (tenant context)."""
    pipeline_service.service_delete_pipeline(
        db,
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)