"""
FastAPI router for List Membership admin endpoints.

Administrators can list, create and delete memberships associated with
lists across tenants.  Collection endpoints are nested under the list
path (``/admin/lists/{list_id}/memberships``) and support optional
``tenant_id`` queries for cross‑tenant filtering.  Singleton endpoints
operate on membership IDs directly (``/admin/memberships/{membership_id}``).

For create and delete operations, the ``X‑User`` header is used to
capture audit information.  All business logic is delegated to the
service layer defined in ``list_membership_service.py`` and
``list_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import list_service, list_membership_service


# Parent router to aggregate collection and singleton sub‑routers
router = APIRouter(tags=["list memberships"])

# ---------------------------------------------------------------------------
# Collection endpoints: /admin/lists/{list_id}/memberships
# ---------------------------------------------------------------------------

collection_router = APIRouter(prefix="/admin/lists/{list_id}/memberships")


@collection_router.get("/", response_model=schemas.PaginationEnvelope[schemas.ListMembershipRead])
def list_memberships(
    *,
    list_id: UUID = Path(..., description="List identifier"),
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier for scoping; omit to ignore tenant filtering"
    ),
    limit: Optional[int] = Query(
        None, ge=1, description="Maximum number of memberships to return"
    ),
    offset: Optional[int] = Query(
        None, ge=0, description="Number of memberships to skip from the beginning"
    ),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.ListMembershipRead]:
    """List memberships for a list (admin context).

    If ``tenant_id`` is provided, the list must belong to that tenant or a
    404 error is raised.  Pagination is optional.
    """
    # Verify list belongs to tenant if tenant_id is supplied
    if tenant_id:
        lst = list_service.get_list(db, list_id, tenant_id)
        if not lst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    items, total = list_membership_service.service_list_memberships(
        db,
        tenant_id=tenant_id,
        list_id=list_id,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[schemas.ListMembershipRead](
        items=items, total=total, limit=limit, offset=offset
    )


@collection_router.post("/", response_model=schemas.ListMembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(
    *,
    list_id: UUID = Path(..., description="List identifier"),
    tenant_id: UUID = Query(..., description="Tenant identifier for the list"),
    membership_in: schemas.ListMembershipCreate,
    x_user: str = Header(
        ..., alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> schemas.ListMembershipRead:
    """Create a new membership under a list (admin context).

    The ``list_id`` in the request body is ignored and overwritten with the
    path parameter to prevent cross‑list associations.
    """
    # Validate list belongs to tenant
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    # Delegate to service; service_create_membership overwrites list_id
    membership = list_membership_service.service_create_membership(
        db,
        tenant_id=tenant_id,
        list_id=list_id,
        membership_in=membership_in,
        created_user=x_user,
    )
    return membership


# ---------------------------------------------------------------------------
# Singleton endpoints: /admin/memberships/{membership_id}
# ---------------------------------------------------------------------------

singleton_router = APIRouter(prefix="/admin/memberships")


@singleton_router.get("/{membership_id}", response_model=schemas.ListMembershipRead)
def get_membership(
    *,
    membership_id: UUID = Path(..., description="Membership identifier"),
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier for scoping; omit to ignore tenant filtering"
    ),
    db: Session = Depends(get_db),
) -> schemas.ListMembershipRead:
    """Retrieve a membership by ID (admin context).

    If ``tenant_id`` is provided, the membership's list must belong to the
    tenant or a 404 error is raised.
    """
    membership = list_membership_service.service_get_membership(db, membership_id=membership_id)
    if tenant_id:
        # Ensure the parent list belongs to tenant
        lst = list_service.get_list(db, membership.list_id, tenant_id)
        if not lst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    return membership


@singleton_router.delete(
    "/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_membership(
    *,
    membership_id: UUID = Path(..., description="Membership identifier"),
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier for scoping; omit to ignore tenant filtering"
    ),
    x_user: Optional[str] = Header(
        None, alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a membership by ID (admin context).

    If ``tenant_id`` is provided, the membership's list must belong to the
    tenant or a 404 error is raised.  The ``X-User`` header is optional
    because delete events do not include user data by default.
    """
    membership = list_membership_service.service_get_membership(db, membership_id=membership_id)
    if tenant_id:
        lst = list_service.get_list(db, membership.list_id, tenant_id)
        if not lst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    # Delegate to service layer.  The tenant_id is passed through
    # directly; if None, the service will still emit an event with a
    # ``None`` tenant header.  Downstream consumers should handle this
    # accordingly.
    list_membership_service.service_delete_membership(
        db,
        tenant_id=tenant_id,
        membership_id=membership_id,
        deleted_user=x_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Include sub‑routers into the parent router
router.include_router(collection_router)
router.include_router(singleton_router)
