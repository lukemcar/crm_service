"""
Tenant‑scoped FastAPI routes for associations.

These endpoints allow tenants to list, create and delete associations that
belong to them.  Each operation delegates to the service layer and
propagates tenant scoping.  Responses are wrapped in the pagination
envelope model where appropriate.  User identifiers for auditing are
accepted via the ``X-User`` header; if absent a default value of
``"anonymous"`` is used.
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
    prefix="/tenants/{tenant_id}/associations",
    tags=["Associations"],
)


@router.get("/", response_model=PaginationEnvelope[AssociationRead])
def list_associations_endpoint(
    tenant_id: UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[AssociationRead]:
    """List associations for a tenant.

    Results are returned in a pagination envelope.
    """
    associations, total = association_service.list_associations(
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
def create_association_endpoint(
    tenant_id: UUID,
    association_in: AssociationCreate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Query(default=None),
) -> AssociationRead:
    """Create a new association for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` is set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    assoc = association_service.create_association(
        db,
        tenant_id=tenant_id,
        association_in=association_in,
        created_user=created_user,
    )
    return AssociationRead.model_validate(assoc, from_attributes=True)


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_association_endpoint(
    tenant_id: UUID,
    association_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an association from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the association does not
    exist or does not belong to the tenant.
    """
    association_service.delete_association(
        db,
        tenant_id=tenant_id,
        association_id=association_id,
    )
    # FastAPI will automatically return a 204 response when None is returned
    return None