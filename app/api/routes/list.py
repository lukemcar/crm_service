"""FastAPI router for List endpoints.

Lists (segments) group CRM records of a specified type.  This router
provides CRUD operations on lists.  Membership management is handled
via a separate router.  Tenancy is enforced through the tenant_id
query parameter.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import list_service


router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/", response_model=List[schemas.ListRead])
def list_lists(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.ListRead]:
    """List all lists for the tenant."""
    return list(list_service.list_lists(db, tenant_id))


@router.post("/", response_model=schemas.ListRead, status_code=status.HTTP_201_CREATED)
def create_list(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    list_in: schemas.ListCreate,
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Create a new list."""
    lst = list_service.create_list(db, tenant_id, user_id, list_in)
    return lst


@router.get("/{list_id}", response_model=schemas.ListRead)
def get_list(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List ID"),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Retrieve a list by ID."""
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return lst


@router.patch("/{list_id}", response_model=schemas.ListRead)
def update_list(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    list_id: UUID = Path(..., description="List ID"),
    list_in: schemas.ListUpdate,
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Update an existing list."""
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    updated = list_service.update_list(db, lst, user_id, list_in)
    return updated


@router.delete(
    "/{list_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_list(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List ID"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a list."""
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    list_service.delete_list(db, lst)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)