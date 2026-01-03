"""
Admin FastAPI routes for activities.

These endpoints allow administrators to manage activities across tenants.
The list endpoint supports optional tenant scoping for cross‑tenant search,
whereas create, update and delete operations require an explicit
``tenant_id`` query parameter.  All auditing uses the ``X-User``
header, defaulting to ``"anonymous"`` when not provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

import app.domain.services.activity_service as activity_service

from app.domain.schemas.activity import ActivityCreate, ActivityUpdate, ActivityRead
from app.domain.schemas.common import PaginationEnvelope

from app.core.db import get_db


router = APIRouter(
    prefix="/admin/activities",
    tags=["Activities"],
)


@router.get("/", response_model=PaginationEnvelope[ActivityRead])
def list_activities_admin(
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope results to a single tenant",
    ),
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[ActivityRead]:
    """List or search activities across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Filters
    perform case‑insensitive matches on type and status.  Results are
    returned in a pagination envelope.
    """
    activities, total = activity_service.service_list_activities(
        db,
        tenant_id=tenant_id,
        type=type,
        status=status,
        limit=limit,
        offset=offset,
    )
    items: List[ActivityRead] = [
        ActivityRead.model_validate(act, from_attributes=True) for act in activities
    ]
    return PaginationEnvelope[ActivityRead](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID for the new activity"),
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Query(default=None),
) -> ActivityRead:
    """Create a new activity for the specified tenant.

    The tenant ID must be supplied as a query parameter.  The caller's
    identity is taken from ``X-User`` header and used for auditing.
    """
    created_user = x_user or "anonymous"
    activity = activity_service.service_create_activity(
        db,
        tenant_id=tenant_id,
        activity_in=activity_in,
        created_user=created_user,
    )
    return ActivityRead.model_validate(activity, from_attributes=True)


@router.put("/{activity_id}", response_model=ActivityRead)
def update_activity_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the activity to update"),
    activity_id: UUID,
    activity_in: ActivityUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Query(default=None),
) -> ActivityRead:
    """Replace an existing activity for the given tenant.

    All fields in the request body replace the current values on the activity.
    Missing fields are set to ``null``.
    """
    modified_user = x_user or "anonymous"
    activity = activity_service.service_update_activity(
        db,
        tenant_id=tenant_id,
        activity_id=activity_id,
        activity_in=activity_in,
        modified_user=modified_user,
    )
    return ActivityRead.model_validate(activity, from_attributes=True)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the activity to delete"),
    activity_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an activity belonging to the given tenant.

    Returns HTTP 204 on success.  Raises 404 if the activity is not found
    or does not belong to the tenant.
    """
    activity_service.service_delete_activity(
        db,
        tenant_id=tenant_id,
        activity_id=activity_id,
    )
    return None