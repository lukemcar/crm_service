"""FastAPI router for Association endpoints.

Associations provide a way to link any two CRM records together.
This router exposes endpoints to list, create, retrieve and delete
associations for a tenant.  Updates are not supported.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import association_service


router = APIRouter(prefix="/associations", tags=["associations"])


@router.get("/", response_model=List[schemas.AssociationRead])
def list_associations(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.AssociationRead]:
    """List all associations for a tenant."""
    return list(association_service.list_associations(db, tenant_id))


@router.post("/", response_model=schemas.AssociationRead, status_code=status.HTTP_201_CREATED)
def create_association(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    association_in: schemas.AssociationCreate,
    db: Session = Depends(get_db),
) -> schemas.AssociationRead:
    """Create a new association."""
    assoc = association_service.create_association(db, tenant_id, user_id, association_in)
    return assoc


@router.get("/{association_id}", response_model=schemas.AssociationRead)
def get_association(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    association_id: UUID = Path(..., description="Association ID"),
    db: Session = Depends(get_db),
) -> schemas.AssociationRead:
    """Retrieve an association by ID."""
    assoc = association_service.get_association(db, association_id, tenant_id)
    if not assoc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")
    return assoc


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_association(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    association_id: UUID = Path(..., description="Association ID"),
    db: Session = Depends(get_db),
) -> None:
    """Delete an association by ID."""
    assoc = association_service.get_association(db, association_id, tenant_id)
    if not assoc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")
    association_service.delete_association(db, assoc)
    return None