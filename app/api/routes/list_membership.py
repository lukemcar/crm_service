"""FastAPI router for List Membership endpoints.

This router manages memberships for lists.  Memberships link lists to
individual CRM records of various types.  Endpoints ensure that the
parent list belongs to the requesting tenant before performing
operations.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import (
    list_service,
    list_membership_service,
)


router = APIRouter(prefix="/lists", tags=["list memberships"])


@router.get("/{list_id}/memberships", response_model=List[schemas.ListMembershipRead])
def list_memberships(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List ID"),
    db: Session = Depends(get_db),
) -> List[schemas.ListMembershipRead]:
    """List all memberships for a list."""
    # Verify list exists for tenant
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return list(list_membership_service.list_memberships(db, list_id))


@router.post("/{list_id}/memberships", response_model=schemas.ListMembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    list_id: UUID = Path(..., description="List ID"),
    membership_in: schemas.ListMembershipCreate,
    db: Session = Depends(get_db),
) -> schemas.ListMembershipRead:
    """Create a new membership for a list."""
    # Ensure the list belongs to the tenant
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    # Enforce that the path list_id is used
    membership_data = membership_in.copy(update={"list_id": list_id})
    membership = list_membership_service.create_membership(db, user_id, membership_data)
    return membership


@router.delete("/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    membership_id: UUID = Path(..., description="Membership ID"),
    db: Session = Depends(get_db),
) -> None:
    """Delete a membership after verifying it belongs to a list in the tenant."""
    membership = list_membership_service.get_membership(db, membership_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    # Verify list for membership belongs to tenant
    lst = list_service.get_list(db, membership.list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    list_membership_service.delete_membership(db, membership)
    return None