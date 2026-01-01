"""
Admin‑scoped endpoints for knowledge base categories.

This router exposes CRUD operations on KB categories across tenants.
Administrators can list categories across tenants (optionally filtering by
tenant), create new categories specifying the tenant, update categories,
and delete categories.  Audit fields are populated from the ``X-User``
header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Path, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_category import (
    AdminCreateKbCategory,
    KbCategoryUpdate,
    KbCategoryOut,
)
from app.domain.services import kb_category_service


router = APIRouter(
    prefix="/admin/kb_categories",
    tags=["Knowledge Base Categories"],
)


@router.get("", response_model=List[KbCategoryOut])
def list_kb_categories_admin_endpoint(
    tenant_id: Optional[UUID] = Query(
        None, description="If provided, filters categories by tenant"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbCategoryOut]:
    """List knowledge base categories across tenants with optional tenant filter."""
    categories, _ = kb_category_service.list_kb_categories(
        db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return [KbCategoryOut.model_validate(c, from_attributes=True) for c in categories]


@router.post("", response_model=KbCategoryOut, status_code=status.HTTP_201_CREATED)
def create_kb_category_admin_endpoint(
    category_in: AdminCreateKbCategory,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbCategoryOut:
    """Create a knowledge base category via the admin API specifying the tenant."""
    created_user = x_user or "anonymous"
    category = kb_category_service.create_kb_category(
        db,
        tenant_id=category_in.tenant_id,
        request=category_in,
        created_by=created_user,
    )
    return KbCategoryOut.model_validate(category, from_attributes=True)


@router.get("/{category_id}", response_model=KbCategoryOut)
def get_kb_category_admin_endpoint(
    category_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the category to scope the search"
    ),
    db: Session = Depends(get_db),
) -> KbCategoryOut:
    """Retrieve a knowledge base category via the admin API."""
    category = kb_category_service.get_kb_category(
        db,
        tenant_id=tenant_id,
        category_id=category_id,
    )
    return KbCategoryOut.model_validate(category, from_attributes=True)


@router.put("/{category_id}", response_model=KbCategoryOut)
def update_kb_category_admin_endpoint(
    category_id: UUID,
    category_update: KbCategoryUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the category to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbCategoryOut:
    """Update a knowledge base category via the admin API."""
    updated_user = x_user or "anonymous"
    category = kb_category_service.update_kb_category(
        db,
        tenant_id=tenant_id,
        category_id=category_id,
        request=category_update,
        updated_by=updated_user,
    )
    return KbCategoryOut.model_validate(category, from_attributes=True)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kb_category_admin_endpoint(
    category_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the category to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a knowledge base category via the admin API."""
    kb_category_service.delete_kb_category(
        db,
        tenant_id=tenant_id,
        category_id=category_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_categories_admin_endpoint",
    "create_kb_category_admin_endpoint",
    "get_kb_category_admin_endpoint",
    "update_kb_category_admin_endpoint",
    "delete_kb_category_admin_endpoint",
]