"""
Admin FastAPI routes for associations.

These endpoints allow administrators to manage associations across tenants.
The list endpoint supports optional tenant scoping for cross‑tenant search,
whereas create and delete operations require an explicit ``tenant_id`` query
parameter.  All auditing uses the ``X-User`` header, defaulting to
``"anonymous"`` when not provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

import app.domain.services.association_service as association_service

from app.domain.schemas.association import AssociationCreate, AssociationRead
from app.domain.schemas.common import PaginationEnvelope

from app.core.db import get_db


router = APIRouter(
    prefix="/admin/associations",
    tags=["Associations"],
)


@router.get("/", response_model=PaginationEnvelope[AssociationRead])
def list_associations_admin(
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope results to a single tenant",
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[AssociationRead]:
    """List associations across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Results
    are returned in a pagination envelope.
    """
    associations, total = association_service.service_list_associations(
        db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    items: List[AssociationRead] = [
        AssociationRead.model_validate(assoc, from_attributes=True) for assoc in associations
    ]
    return PaginationEnvelope[AssociationRead](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=AssociationRead, status_code=status.HTTP_201_CREATED)
def create_association_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID for the new association"),
    association_in: AssociationCreate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Query(default=None),
) -> AssociationRead:
    """Create a new association for the specified tenant.

    The tenant ID must be supplied as a query parameter.  The caller's
    identity is taken from ``X-User`` header and used for auditing.
    """
    created_user = x_user or "anonymous"
    assoc = association_service.service_create_association(
        db,
        tenant_id=tenant_id,
        association_in=association_in,
        created_user=created_user,
    )
    return AssociationRead.model_validate(assoc, from_attributes=True)


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_association_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the association to delete"),
    association_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an association belonging to the given tenant.

    Returns HTTP 204 on success.  Raises 404 if the association is not found
    or does not belong to the tenant.
    """
    association_service.service_delete_association(
        db,
        tenant_id=tenant_id,
        association_id=association_id,
    )
    return None