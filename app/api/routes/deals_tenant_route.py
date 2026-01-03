"""
Tenant FastAPI routes for deals.

These endpoints allow tenants to manage their own deals.  Listing and
mutating endpoints are scoped to the tenant via the path parameter.
Audit fields use the ``X-User`` header and default to ``"anonymous"``.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response, status
from sqlalchemy.orm import Session

import app.domain.services.deal_service as deal_service
import app.domain.services.pipeline_service as pipeline_service
import app.domain.services.pipeline_stage_service as pipeline_stage_service

from app.domain.schemas.deal import DealCreate, DealUpdate, DealRead
from app.domain.schemas.common import PaginationEnvelope
from app.core.db import get_db

router = APIRouter(
    prefix="/tenants/{tenant_id}/deals",
    tags=["Deals"],
)


@router.get("/", response_model=PaginationEnvelope[DealRead])
def list_deals_tenant(
    *,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    pipeline_id: Optional[UUID] = Query(None, description="Optional pipeline ID filter"),
    stage_id: Optional[UUID] = Query(None, description="Optional stage ID filter"),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[DealRead]:
    """List or search deals for a single tenant with optional filters and pagination."""
    deals, total = deal_service.service_list_deals(
        db,
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        limit=limit,
        offset=offset,
    )
    items: List[DealRead] = [DealRead.model_validate(dl, from_attributes=True) for dl in deals]
    return PaginationEnvelope[DealRead](items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=DealRead, status_code=status.HTTP_201_CREATED)
def create_deal_tenant(
    *,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    deal_in: DealCreate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> DealRead:
    """Create a new deal for the specified tenant.

    Validates that the referenced pipeline and stage belong to the tenant before
    delegating to the service layer.  Audit fields are populated from the
    ``X-User`` header.
    """
    # Validate pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, deal_in.pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    # Validate stage exists and belongs to the specified pipeline
    stage = pipeline_stage_service.get_stage(db, deal_in.stage_id)
    if not stage or stage.pipeline_id != deal_in.pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found in pipeline")
    created_user = x_user or "anonymous"
    deal = deal_service.service_create_deal(
        db,
        tenant_id=tenant_id,
        deal_in=deal_in,
        created_user=created_user,
    )
    return DealRead.model_validate(deal, from_attributes=True)


@router.put("/{deal_id}", response_model=DealRead)
def update_deal_tenant(
    *,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    deal_id: UUID = Path(..., description="Deal ID"),
    deal_in: DealUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> DealRead:
    """Replace an existing deal for the given tenant.

    Validates pipeline and stage updates before performing the update.  Missing
    fields remain unchanged.  Audit fields are populated from the ``X-User``
    header.
    """
    # Retrieve the current deal to determine existing pipeline/stage for validation
    current_deal = deal_service.service_get_deal(db, tenant_id=tenant_id, deal_id=deal_id)
    # Determine the new pipeline and stage IDs (use current if not updated)
    new_pipeline_id = deal_in.pipeline_id or current_deal.pipeline_id
    new_stage_id = deal_in.stage_id or current_deal.stage_id
    # Validate pipeline belongs to tenant
    pipeline = pipeline_service.get_pipeline(db, new_pipeline_id, tenant_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    # Validate stage belongs to the pipeline
    stage = pipeline_stage_service.get_stage(db, new_stage_id)
    if not stage or stage.pipeline_id != new_pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found in pipeline")
    modified_user = x_user or "anonymous"
    updated = deal_service.service_update_deal(
        db,
        tenant_id=tenant_id,
        deal_id=deal_id,
        deal_in=deal_in,
        modified_user=modified_user,
    )
    return DealRead.model_validate(updated, from_attributes=True)


@router.delete(
    "/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_deal_tenant(
    *,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    deal_id: UUID = Path(..., description="Deal ID"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a deal belonging to the given tenant.

    Returns HTTP 204 on success.  Raises 404 if the deal is not found or
    does not belong to the tenant.
    """
    deal_service.service_delete_deal(db, tenant_id=tenant_id, deal_id=deal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)