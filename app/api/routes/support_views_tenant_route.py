"""
Tenant‑scoped FastAPI routes for support views.

These endpoints allow tenants to manage support views that define
filters and sort orders for ticket lists.  Agents can create, update,
retrieve, list and delete views within their tenant context.  Audit
fields are populated using the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services import support_view_service
from app.domain.schemas.support_view import (
    TenantCreateSupportView,
    SupportViewUpdate,
    SupportViewOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/support_views",
    tags=["SupportViews"],
)


@router.get("/", response_model=PaginationEnvelope[SupportViewOut])
def list_support_views_endpoint(
    tenant_id: UUID,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SupportViewOut]:
    """List support views for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of views.
    """
    views, total = support_view_service.list_support_views(
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
def create_support_view_endpoint(
    tenant_id: UUID,
    view_in: TenantCreateSupportView,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SupportViewOut:
    """Create a new support view for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the view are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    view = support_view_service.create_support_view(
        db,
        tenant_id=tenant_id,
        request=view_in,
        created_by=created_user,
    )
    return SupportViewOut.model_validate(view, from_attributes=True)


@router.patch("/{view_id}", response_model=SupportViewOut)
def update_support_view_endpoint(
    tenant_id: UUID,
    view_id: UUID,
    view_update: SupportViewUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SupportViewOut:
    """Update an existing support view.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    view = support_view_service.update_support_view(
        db,
        tenant_id=tenant_id,
        view_id=view_id,
        request=view_update,
        updated_by=updated_user,
    )
    return SupportViewOut.model_validate(view, from_attributes=True)


@router.get("/{view_id}", response_model=SupportViewOut)
def get_support_view_endpoint(
    tenant_id: UUID,
    view_id: UUID,
    db: Session = Depends(get_db),
) -> SupportViewOut:
    """Retrieve a single support view by ID within a tenant.

    Raises 404 if the view does not exist or does not belong to
    the tenant.
    """
    view = support_view_service.get_support_view(
        db, tenant_id=tenant_id, view_id=view_id
    )
    return SupportViewOut.model_validate(view, from_attributes=True)


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_support_view_endpoint(
    tenant_id: UUID,
    view_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a support view from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the view does not
    exist or does not belong to the tenant.  The ``X-User`` header is
    currently ignored for deletion events; event publishers do not
    include user information for deletions.
    """
    support_view_service.delete_support_view(
        db, tenant_id=tenant_id, view_id=view_id
    )
    return None