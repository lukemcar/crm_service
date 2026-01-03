"""
Tenant‑scoped FastAPI routes for activities.

These endpoints allow tenants to list, create, update and delete
activities that belong to them.  Each operation delegates to the service
layer and propagates tenant scoping.  Responses are wrapped in the
pagination envelope model where appropriate.  User identifiers for
auditing are accepted via the ``X-User`` header; if absent a default
value of ``"anonymous"`` is used.
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
    prefix="/tenants/{tenant_id}/activities",
    tags=["Activities"],
)


@router.get("/", response_model=PaginationEnvelope[ActivityRead])
def list_activities_endpoint(
    tenant_id: UUID,
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[ActivityRead]:
    """List or search activities for a tenant.

    Filters are optional and perform case‑insensitive matches on type and
    status.  Results are ordered by creation date descending and wrapped
    in a pagination envelope.
    """
    activities, total = activity_service.list_activities(
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
def create_activity_endpoint(
    tenant_id: UUID,
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Query(default=None),
) -> ActivityRead:
    """Create a new activity for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` are set
    to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    activity = activity_service.create_activity(
        db,
        tenant_id=tenant_id,
        activity_in=activity_in,
        created_user=created_user,
    )
    return ActivityRead.model_validate(activity, from_attributes=True)


@router.put("/{activity_id}", response_model=ActivityRead)
def update_activity_endpoint(
    tenant_id: UUID,
    activity_id: UUID,
    activity_in: ActivityUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Query(default=None),
) -> ActivityRead:
    """Replace an existing activity.

    All fields in the request body will replace the current values on
    the activity.  Missing fields will be set to ``null``.
    """
    modified_user = x_user or "anonymous"
    activity = activity_service.update_activity(
        db,
        tenant_id=tenant_id,
        activity_id=activity_id,
        activity_in=activity_in,
        modified_user=modified_user,
    )
    return ActivityRead.model_validate(activity, from_attributes=True)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_endpoint(
    tenant_id: UUID,
    activity_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an activity from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the activity does not
    exist or does not belong to the tenant.
    """
    activity_service.delete_activity(
        db,
        tenant_id=tenant_id,
        activity_id=activity_id,
    )
    # FastAPI will automatically return a 204 response when None is returned
    return None