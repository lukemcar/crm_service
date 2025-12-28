"""FastAPI router for Activity endpoints.

Provides CRUD operations on activities.  Activities are tenant scoped
and can represent notes or tasks.  Endpoints require a tenant_id
query parameter to enforce multi‑tenancy.  In a real environment,
tenant and user identifiers would be extracted from JWT claims.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import activity_service


router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/", response_model=List[schemas.ActivityRead])
def list_activities(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.ActivityRead]:
    """List all activities for a tenant."""
    return list(activity_service.list_activities(db, tenant_id))


@router.post("/", response_model=schemas.ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    activity_in: schemas.ActivityCreate,
    db: Session = Depends(get_db),
) -> schemas.ActivityRead:
    """Create a new activity."""
    activity = activity_service.create_activity(db, tenant_id, user_id, activity_in)
    return activity


@router.get("/{activity_id}", response_model=schemas.ActivityRead)
def get_activity(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    activity_id: UUID = Path(..., description="Activity ID"),
    db: Session = Depends(get_db),
) -> schemas.ActivityRead:
    """Retrieve an activity by ID."""
    activity = activity_service.get_activity(db, activity_id, tenant_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


@router.patch("/{activity_id}", response_model=schemas.ActivityRead)
def update_activity(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    activity_id: UUID = Path(..., description="Activity ID"),
    activity_in: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
) -> schemas.ActivityRead:
    """Update an activity."""
    activity = activity_service.get_activity(db, activity_id, tenant_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    updated = activity_service.update_activity(db, activity, user_id, activity_in)
    return updated


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    activity_id: UUID = Path(..., description="Activity ID"),
    db: Session = Depends(get_db),
) -> None:
    """Delete an activity."""
    activity = activity_service.get_activity(db, activity_id, tenant_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    activity_service.delete_activity(db, activity)
    return None