"""
FastAPI router for List Membership tenant endpoints.

Tenant routes expose collection and singleton endpoints for memberships
owned by lists.  All paths embed the tenant identifier in the URL to
enforce isolation.  Collection endpoints are nested under lists
(``/tenants/{tenant_id}/lists/{list_id}/memberships``) while
singleton endpoints live at
``/tenants/{tenant_id}/memberships/{membership_id}``.

Mutating operations accept an ``X‑User`` header to capture audit
information.  Business logic is delegated to the service layer
``list_membership_service.py`` and ``list_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import list_service, list_membership_service


# Parent router for tenant list membership endpoints
router = APIRouter(tags=["list memberships"])

# ---------------------------------------------------------------------------
# Collection endpoints: /tenants/{tenant_id}/lists/{list_id}/memberships
# ---------------------------------------------------------------------------

collection_router = APIRouter(prefix="/tenants/{tenant_id}/lists/{list_id}/memberships")


@collection_router.get("/", response_model=schemas.PaginationEnvelope[schemas.ListMembershipRead])
def list_memberships(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List identifier"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of memberships to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of memberships to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.ListMembershipRead]:
    """List memberships for a list (tenant context).

    Verifies that the list exists and belongs to the tenant.  Pagination
    parameters are optional.
    """
    # Verify list belongs to tenant
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List identifier"),
    membership_in: schemas.ListMembershipCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.ListMembershipRead:
    """Create a membership under a list (tenant context).

    Ignores the ``list_id`` field in the request body and uses the path
    parameter instead.  Raises a 404 error if the list does not
    belong to the tenant.
    """
    # Validate list belongs to tenant
    lst = list_service.get_list(db, list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    membership = list_membership_service.service_create_membership(
        db,
        tenant_id=tenant_id,
        list_id=list_id,
        membership_in=membership_in,
        created_user=x_user,
    )
    return membership


# ---------------------------------------------------------------------------
# Singleton endpoints: /tenants/{tenant_id}/memberships/{membership_id}
# ---------------------------------------------------------------------------

singleton_router = APIRouter(prefix="/tenants/{tenant_id}/memberships")


@singleton_router.get("/{membership_id}", response_model=schemas.ListMembershipRead)
def get_membership(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    membership_id: UUID = Path(..., description="Membership identifier"),
    db: Session = Depends(get_db),
) -> schemas.ListMembershipRead:
    """Retrieve a membership by ID (tenant context).

    Ensures the membership's parent list belongs to the tenant.
    """
    membership = list_membership_service.service_get_membership(db, membership_id=membership_id)
    # Validate the membership's list belongs to the tenant
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    membership_id: UUID = Path(..., description="Membership identifier"),
    x_user: Optional[str] = Header(
        None, alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a membership (tenant context).

    Ensures the membership's list belongs to the tenant before
    delegating the deletion to the service layer.  The ``X-User``
    header is optional because deletion events do not include user
    information by default.
    """
    membership = list_membership_service.service_get_membership(db, membership_id=membership_id)
    lst = list_service.get_list(db, membership.list_id, tenant_id)
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    list_membership_service.service_delete_membership(
        db,
        tenant_id=tenant_id,
        membership_id=membership_id,
        deleted_user=x_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Attach sub‑routers to the parent router
router.include_router(collection_router)
router.include_router(singleton_router)