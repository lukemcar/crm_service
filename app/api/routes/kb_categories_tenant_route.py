"""
Tenant‑scoped endpoints for knowledge base categories.

This router exposes CRUD operations on knowledge base categories within a
tenant.  Tenants can list, create, update and delete categories.
Audit fields are populated from the ``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_category import (
    TenantCreateKbCategory,
    KbCategoryUpdate,
    KbCategoryOut,
)
from app.domain.services import kb_category_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/kb_categories",
    tags=["Knowledge Base Categories"],
)


@router.get("", response_model=List[KbCategoryOut])
def list_kb_categories_tenant_endpoint(
    tenant_id: UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbCategoryOut]:
    """List knowledge base categories for a tenant."""
    categories, _ = kb_category_service.list_kb_categories(
        db, tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [KbCategoryOut.model_validate(c, from_attributes=True) for c in categories]


@router.post("", response_model=KbCategoryOut, status_code=status.HTTP_201_CREATED)
def create_kb_category_tenant_endpoint(
    tenant_id: UUID,
    category_in: TenantCreateKbCategory,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbCategoryOut:
    """Create a knowledge base category within a tenant."""
    created_user = x_user or "anonymous"
    category = kb_category_service.create_kb_category(
        db,
        tenant_id=tenant_id,
        request=category_in,
        created_by=created_user,
    )
    return KbCategoryOut.model_validate(category, from_attributes=True)


@router.get("/{category_id}", response_model=KbCategoryOut)
def get_kb_category_tenant_endpoint(
    tenant_id: UUID,
    category_id: UUID,
    db: Session = Depends(get_db),
) -> KbCategoryOut:
    """Retrieve a knowledge base category within a tenant."""
    category = kb_category_service.get_kb_category(
        db, tenant_id=tenant_id, category_id=category_id
    )
    return KbCategoryOut.model_validate(category, from_attributes=True)


@router.put("/{category_id}", response_model=KbCategoryOut)
def update_kb_category_tenant_endpoint(
    tenant_id: UUID,
    category_id: UUID,
    category_update: KbCategoryUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> KbCategoryOut:
    """Update a knowledge base category within a tenant."""
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
def delete_kb_category_tenant_endpoint(
    tenant_id: UUID,
    category_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a knowledge base category within a tenant."""
    kb_category_service.delete_kb_category(
        db,
        tenant_id=tenant_id,
        category_id=category_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_categories_tenant_endpoint",
    "create_kb_category_tenant_endpoint",
    "get_kb_category_tenant_endpoint",
    "update_kb_category_tenant_endpoint",
    "delete_kb_category_tenant_endpoint",
]