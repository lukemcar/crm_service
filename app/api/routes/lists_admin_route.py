"""
FastAPI router for List admin endpoints.

This module defines admin routes for managing lists.  Admin routes are
prefixed with ``/admin/lists`` and allow for cross‑tenant listing of
lists with optional filters.  Mutating operations require an explicit
``tenant_id`` query parameter and use the ``X‑User`` header to
populate audit fields.  All endpoints delegate business logic to the
service layer defined in ``list_service.py`` and return Pydantic
schemas for consistent API contracts.

The standard pagination envelope is used for list responses.  See
``app/domain/schemas/common.py`` for details.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import list_service


# Router with ``/admin/lists`` prefix.  Tag name aligns with other
# domain routers.
router = APIRouter(prefix="/admin/lists", tags=["lists"])


@router.get("/", response_model=schemas.PaginationEnvelope[schemas.ListRead])
def list_lists(
    *,
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier to scope lists; omit to list all tenants"
    ),
    name: Optional[str] = Query(
        None, description="Filter lists by name (case‑insensitive, substring match)"
    ),
    object_type: Optional[str] = Query(
        None, description="Filter by the object type associated with the list"
    ),
    list_type: Optional[str] = Query(
        None, description="Filter by list type (e.g. static, dynamic)"
    ),
    limit: Optional[int] = Query(
        None, ge=1, description="Maximum number of lists to return"
    ),
    offset: Optional[int] = Query(
        None, ge=0, description="Number of lists to skip from the beginning"
    ),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.ListRead]:
    """List lists across tenants with optional filters and pagination.

    When ``tenant_id`` is provided, results are scoped to that tenant.  The
    ``name`` filter performs a case‑insensitive substring search.  ``object_type``
    and ``list_type`` filters must match exactly.  Pagination is optional;
    if ``limit`` or ``offset`` is omitted, all matching records are returned.
    """
    items, total = list_service.service_list_lists(
        db,
        tenant_id=tenant_id,
        name=name,
        object_type=object_type,
        list_type=list_type,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[schemas.ListRead](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=schemas.ListRead, status_code=status.HTTP_201_CREATED)
def create_list(
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant identifier for which to create the list"
    ),
    list_in: schemas.ListCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Create a new list for a tenant.

    The caller must provide a ``tenant_id`` and a valid ``ListCreate`` body.
    Audit fields are populated from the ``X-User`` header.
    """
    lst = list_service.service_create_list(
        db,
        tenant_id=tenant_id,
        list_in=list_in,
        created_user=x_user,
    )
    return lst


@router.get("/{list_id}", response_model=schemas.ListRead)
def get_list(
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant identifier that owns the list"
    ),
    list_id: UUID = Path(..., description="List identifier"),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Retrieve a list by ID within a tenant."""
    return list_service.service_get_list(
        db, tenant_id=tenant_id, list_id=list_id
    )


@router.patch("/{list_id}", response_model=schemas.ListRead)
def update_list(
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant identifier that owns the list"
    ),
    list_id: UUID = Path(..., description="List identifier"),
    list_in: schemas.ListUpdate,
    x_user: str = Header(
        ..., alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Update an existing list.

    Only fields provided in ``list_in`` are updated.  Audit information is
    populated from the ``X-User`` header.  If no changes are detected,
    the service will still return the list but no update event will be
    emitted.
    """
    return list_service.service_update_list(
        db,
        tenant_id=tenant_id,
        list_id=list_id,
        list_in=list_in,
        modified_user=x_user,
    )


@router.delete(
    "/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_list(
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant identifier that owns the list"
    ),
    list_id: UUID = Path(..., description="List identifier"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a list.  A deletion event is emitted after commit."""
    list_service.service_delete_list(
        db, tenant_id=tenant_id, list_id=list_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)