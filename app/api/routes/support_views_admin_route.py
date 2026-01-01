"""
Admin FastAPI routes for support views.

These endpoints allow administrators to manage support views across
tenants.  Listing supports optional tenant scoping for cross‑tenant
searches.  Create and mutation operations require an explicit
``tenant_id`` in the request body or query parameter to ensure that
the operation applies within the correct tenant.  Audit fields are
populated from the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.support_view_service import (
    list_support_views as service_list_support_views,
    create_support_view as service_create_support_view,
    update_support_view as service_update_support_view,
    get_support_view as service_get_support_view,
    delete_support_view as service_delete_support_view,
)
from app.domain.schemas.support_view import (
    AdminCreateSupportView,
    SupportViewUpdate,
    SupportViewOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/support_views",
    tags=["SupportViews"],
)


@router.get("/", response_model=PaginationEnvelope[SupportViewOut])
def list_support_views_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SupportViewOut]:
    """List or search support views across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Filters perform exact matches on ``is_active``.  Results are
    ordered by creation date descending and wrapped in a pagination
    envelope.  The total matching count is included.
    """
    views, total = service_list_support_views(
        db,
        tenant_id=tenant_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items: List[SupportViewOut] = [
        SupportViewOut.model_validate(v, from_attributes=True) for v in views
    ]
    return PaginationEnvelope[SupportViewOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=SupportViewOut, status_code=status.HTTP_201_CREATED)
def create_support_view_admin(
    *,
    view_in: AdminCreateSupportView,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> SupportViewOut:
    """Create a new support view on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateSupportView``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    view = service_create_support_view(
        db,
        tenant_id=view_in.tenant_id,
        request=view_in,
        created_by=created_user,
    )
    return SupportViewOut.model_validate(view, from_attributes=True)


@router.patch("/{view_id}", response_model=SupportViewOut)
def update_support_view_admin(
    *,
    view_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the support view to update"
    ),
    view_update: SupportViewUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> SupportViewOut:
    """Apply updates to a support view as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    view = service_update_support_view(
        db,
        tenant_id=tenant_id,
        view_id=view_id,
        request=view_update,
        updated_by=updated_user,
    )
    return SupportViewOut.model_validate(view, from_attributes=True)


@router.get("/{view_id}", response_model=SupportViewOut)
def get_support_view_admin(
    *,
    view_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the support view to retrieve"
    ),
    db: Session = Depends(get_db),
) -> SupportViewOut:
    """Retrieve a support view across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    view can be resolved in the correct tenant context.  Raises 404
    if the view does not exist in the tenant.
    """
    view = service_get_support_view(
        db, tenant_id=tenant_id, view_id=view_id
    )
    return SupportViewOut.model_validate(view, from_attributes=True)


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_support_view_admin(
    *,
    view_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the support view to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a support view as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_support_view(
        db, tenant_id=tenant_id, view_id=view_id
    )
    return None