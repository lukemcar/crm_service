"""
Tenant‑scoped FastAPI routes for group profiles.

These endpoints allow tenants to list, create, update, retrieve and
delete group profiles that belong to them.  Group profiles encode
support queue metadata such as default SLA policies, routing
configuration and AI work mode.  Audit fields are populated using
the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services import group_profile_service  # for mypy namespace support
from app.domain.schemas.group_profile import (
    TenantCreateGroupProfile,
    GroupProfileUpdate,
    GroupProfileOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/group_profiles",
    tags=["GroupProfiles"],
)


@router.get("/", response_model=PaginationEnvelope[GroupProfileOut])
def list_group_profiles_endpoint(
    tenant_id: UUID,
    profile_type: Optional[str] = None,
    is_support_queue: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[GroupProfileOut]:
    """List group profiles for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of profiles.
    """
    profiles, total = group_profile_service.list_group_profiles(
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
def create_group_profile_endpoint(
    tenant_id: UUID,
    profile_in: TenantCreateGroupProfile,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> GroupProfileOut:
    """Create a new group profile for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the profile are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    profile = group_profile_service.create_group_profile(
        db,
        tenant_id=tenant_id,
        request=profile_in,
        created_by=created_user,
    )
    return GroupProfileOut.model_validate(profile, from_attributes=True)


@router.patch("/{profile_id}", response_model=GroupProfileOut)
def update_group_profile_endpoint(
    tenant_id: UUID,
    profile_id: UUID,
    profile_update: GroupProfileUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> GroupProfileOut:
    """Update an existing group profile.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    profile = group_profile_service.update_group_profile(
        db,
        tenant_id=tenant_id,
        profile_id=profile_id,
        request=profile_update,
        updated_by=updated_user,
    )
    return GroupProfileOut.model_validate(profile, from_attributes=True)


@router.get("/{profile_id}", response_model=GroupProfileOut)
def get_group_profile_endpoint(
    tenant_id: UUID,
    profile_id: UUID,
    db: Session = Depends(get_db),
) -> GroupProfileOut:
    """Retrieve a single group profile by ID within a tenant.

    Raises 404 if the profile does not exist or does not belong to
    the tenant.
    """
    profile = group_profile_service.get_group_profile(
        db, tenant_id=tenant_id, profile_id=profile_id
    )
    return GroupProfileOut.model_validate(profile, from_attributes=True)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_profile_endpoint(
    tenant_id: UUID,
    profile_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a group profile from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the profile does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events; event publishers
    do not include user information for deletions.
    """
    group_profile_service.delete_group_profile(
        db, tenant_id=tenant_id, profile_id=profile_id
    )
    return None
