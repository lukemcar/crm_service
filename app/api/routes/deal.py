"""FastAPI router for Deal endpoints.

Defines CRUD operations for deals.  Deals belong to a tenant and
reference a pipeline and stage.  Endpoints verify that the referenced
pipeline and stage exist within the tenant before creating or
updating deals.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import (
    deal_service,
    pipeline_service,
    pipeline_stage_service,
)


router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/", response_model=List[schemas.DealRead])
def list_deals(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.DealRead]:
    """List all deals for a given tenant."""
    return deal_service.list_deals(db, tenant_id)


@router.post("/", response_model=schemas.DealRead, status_code=status.HTTP_201_CREATED)
def create_deal(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    deal_in: schemas.DealCreate,
    db: Session = Depends(get_db),
) -> schemas.DealRead:
    """Create a new deal after validating pipeline and stage."""
    # Validate pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, deal_in.pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    # Validate stage exists and belongs to same pipeline
    stage = pipeline_stage_service.get_stage(db, deal_in.stage_id)
    if not stage or stage.pipeline_id != deal_in.pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found in pipeline")
    deal = deal_service.create_deal(db, tenant_id, user_id, deal_in)
    return deal


@router.get("/{deal_id}", response_model=schemas.DealRead)
def get_deal(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    deal_id: UUID = Path(..., description="Deal ID"),
    db: Session = Depends(get_db),
) -> schemas.DealRead:
    """Retrieve a deal by ID."""
    deal = deal_service.get_deal(db, deal_id, tenant_id)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal


@router.patch("/{deal_id}", response_model=schemas.DealRead)
def update_deal(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    deal_id: UUID = Path(..., description="Deal ID"),
    deal_in: schemas.DealUpdate,
    db: Session = Depends(get_db),
) -> schemas.DealRead:
    """Update an existing deal.  Validates any updated pipeline or stage."""
    deal_obj = deal_service.get_deal(db, deal_id, tenant_id)
    if not deal_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    # If pipeline or stage are being updated, validate them
    new_pipeline_id = deal_in.pipeline_id or deal_obj.pipeline_id
    new_stage_id = deal_in.stage_id or deal_obj.stage_id
    # Check pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, new_pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    # Check stage belongs to pipeline
    stage = pipeline_stage_service.get_stage(db, new_stage_id)
    if not stage or stage.pipeline_id != new_pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found in pipeline")
    updated = deal_service.update_deal(db, deal_obj, user_id, deal_in)
    return updated


@router.delete(
    "/{deal_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_deal(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    deal_id: UUID = Path(..., description="Deal ID"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a deal by ID."""
    deal = deal_service.get_deal(db, deal_id, tenant_id)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    deal_service.delete_deal(db, deal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
