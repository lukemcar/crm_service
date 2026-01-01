"""
Admin FastAPI routes for group profiles.

These endpoints allow administrators to list, create, update, retrieve
and delete group profiles across tenants.  Listing supports
optional tenant scoping for cross‑tenant searches.  Create and
mutation operations require an explicit ``tenant_id`` in the request
body or query parameter to ensure that the operation applies within
the correct tenant.  Audit fields are populated from the ``X-User``
header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.group_profile_service import (
    list_group_profiles as service_list_group_profiles,
    create_group_profile as service_create_group_profile,
    update_group_profile as service_update_group_profile,
    get_group_profile as service_get_group_profile,
    delete_group_profile as service_delete_group_profile,
)
from app.domain.schemas.group_profile import (
    AdminCreateGroupProfile,
    GroupProfileUpdate,
    GroupProfileOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/group_profiles",
    tags=["GroupProfiles"],
)


@router.get("/", response_model=PaginationEnvelope[GroupProfileOut])
def list_group_profiles_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    profile_type: Optional[str] = None,
    is_support_queue: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[GroupProfileOut]:
    """List or search group profiles across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Filters perform exact matches on profile_type and is_support_queue.
    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  The total matching count is included.
    """
    profiles, total = service_list_group_profiles(
        db,
        tenant_id=tenant_id,
        profile_type=profile_type,
        is_support_queue=is_support_queue,
        limit=limit,
        offset=offset,
    )
    items: List[GroupProfileOut] = [
        GroupProfileOut.model_validate(p, from_attributes=True) for p in profiles
    ]
    return PaginationEnvelope[GroupProfileOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=GroupProfileOut, status_code=status.HTTP_201_CREATED)
def create_group_profile_admin(
    *,
    profile_in: AdminCreateGroupProfile,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> GroupProfileOut:
    """Create a new group profile on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateGroupProfile``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    profile = service_create_group_profile(
        db,
        tenant_id=profile_in.tenant_id,
        request=profile_in,
        created_by=created_user,
    )
    return GroupProfileOut.model_validate(profile, from_attributes=True)


@router.patch("/{profile_id}", response_model=GroupProfileOut)
def update_group_profile_admin(
    *,
    profile_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the group profile to update"
    ),
    profile_update: GroupProfileUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> GroupProfileOut:
    """Apply updates to a group profile as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    profile = service_update_group_profile(
        db,
        tenant_id=tenant_id,
        profile_id=profile_id,
        request=profile_update,
        updated_by=updated_user,
    )
    return GroupProfileOut.model_validate(profile, from_attributes=True)


@router.get("/{profile_id}", response_model=GroupProfileOut)
def get_group_profile_admin(
    *,
    profile_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the group profile to retrieve"
    ),
    db: Session = Depends(get_db),
) -> GroupProfileOut:
    """Retrieve a group profile across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    profile can be resolved in the correct tenant context.  Raises 404
    if the profile does not exist in the tenant.
    """
    profile = service_get_group_profile(
        db, tenant_id=tenant_id, profile_id=profile_id
    )
    return GroupProfileOut.model_validate(profile, from_attributes=True)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_profile_admin(
    *,
    profile_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the group profile to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a group profile as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_group_profile(
        db, tenant_id=tenant_id, profile_id=profile_id
    )
    return None
