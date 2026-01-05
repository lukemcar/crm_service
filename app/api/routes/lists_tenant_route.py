"""
FastAPI router for List tenant endpoints.

These endpoints manage lists within a specific tenant.  The tenant
identifier is embedded in the path (``/tenants/{tenant_id}/lists``),
eliminating the need for a query parameter.  All operations are
restricted to the given tenant and use the ``X‑User`` header for
auditing purposes.  Results are returned using Pydantic schemas and
pagination envelopes for consistency.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import list_service


router = APIRouter(prefix="/tenants/{tenant_id}/lists", tags=["lists"])


@router.get("/", response_model=schemas.PaginationEnvelope[schemas.ListRead])
def list_lists(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    name: Optional[str] = Query(
        None, description="Filter lists by name (case‑insensitive, substring match)"
    ),
    object_type: Optional[str] = Query(
        None, description="Filter by the object type associated with the list"
    ),
    list_type: Optional[str] = Query(
        None, description="Filter by list type (e.g. static, dynamic)"
    ),
    processing_type: Optional[str] = Query(
        None, description="Filter by processing type (e.g. STATIC)"
    ),
    is_archived: Optional[bool] = Query(
        None, description="Filter by archived status (true/false)"
    ),
    limit: Optional[int] = Query(
        None, ge=1, description="Maximum number of lists to return"
    ),
    offset: Optional[int] = Query(
        None, ge=0, description="Number of lists to skip from the beginning"
    ),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[schemas.ListRead]:
    """List lists for a single tenant with optional filters and pagination."""
    items, total = list_service.service_list_lists(
        db,
        tenant_id=tenant_id,
        name=name,
        object_type=object_type,
        list_type=list_type,
        processing_type=processing_type,
        is_archived=is_archived,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[schemas.ListRead](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=schemas.ListRead, status_code=status.HTTP_201_CREATED)
def create_list(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    list_in: schemas.ListCreate,
    x_user: str = Header(..., alias="X-User", description="User performing the operation"),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Create a new list for the tenant."""
    return list_service.service_create_list(
        db,
        tenant_id=tenant_id,
        list_in=list_in,
        created_user=x_user,
    )


@router.get("/{list_id}", response_model=schemas.ListRead)
def get_list(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List identifier"),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Retrieve a list within the tenant."""
    return list_service.service_get_list(
        db, tenant_id=tenant_id, list_id=list_id
    )


@router.patch("/{list_id}", response_model=schemas.ListRead)
def update_list(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List identifier"),
    list_in: schemas.ListUpdate,
    x_user: str = Header(
        ..., alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> schemas.ListRead:
    """Update an existing list within the tenant."""
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
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    list_id: UUID = Path(..., description="List identifier"),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a list within the tenant."""
    list_service.service_delete_list(
        db, tenant_id=tenant_id, list_id=list_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)