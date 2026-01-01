"""
Admin‑scoped endpoints for knowledge base sections.

This router exposes CRUD operations on KB sections across tenants.
Administrators can list sections (optionally filtering by tenant or category),
create sections specifying the tenant, update sections, and delete sections.
Audit fields are populated from the ``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Path, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.kb_section import (
    AdminCreateKbSection,
    KbSectionUpdate,
    KbSectionOut,
)
from app.domain.services import kb_section_service


router = APIRouter(
    prefix="/admin/kb_sections",
    tags=["Knowledge Base Sections"],
)


@router.get("", response_model=List[KbSectionOut])
def list_kb_sections_admin_endpoint(
    tenant_id: Optional[UUID] = Query(
        None, description="If provided, filters sections by tenant"
    ),
    kb_category_id: Optional[UUID] = Query(
        None, description="If provided, filters sections by category"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[KbSectionOut]:
    """List knowledge base sections across tenants with optional filters."""
    sections, _ = kb_section_service.list_kb_sections(
        db,
        tenant_id=tenant_id,
        kb_category_id=kb_category_id,
        limit=limit,
        offset=offset,
    )
    return [KbSectionOut.model_validate(s, from_attributes=True) for s in sections]


@router.post("", response_model=KbSectionOut, status_code=status.HTTP_201_CREATED)
def create_kb_section_admin_endpoint(
    section_in: AdminCreateKbSection,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbSectionOut:
    """Create a knowledge base section via the admin API specifying the tenant."""
    created_user = x_user or "anonymous"
    section = kb_section_service.create_kb_section(
        db,
        tenant_id=section_in.tenant_id,
        request=section_in,
        created_by=created_user,
    )
    return KbSectionOut.model_validate(section, from_attributes=True)


@router.get("/{section_id}", response_model=KbSectionOut)
def get_kb_section_admin_endpoint(
    section_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the section to scope the search"
    ),
    db: Session = Depends(get_db),
) -> KbSectionOut:
    """Retrieve a knowledge base section via the admin API."""
    section = kb_section_service.get_kb_section(
        db,
        tenant_id=tenant_id,
        section_id=section_id,
    )
    return KbSectionOut.model_validate(section, from_attributes=True)


@router.put("/{section_id}", response_model=KbSectionOut)
def update_kb_section_admin_endpoint(
    section_id: UUID,
    section_update: KbSectionUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the section to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> KbSectionOut:
    """Update a knowledge base section via the admin API."""
    updated_user = x_user or "anonymous"
    section = kb_section_service.update_kb_section(
        db,
        tenant_id=tenant_id,
        section_id=section_id,
        request=section_update,
        updated_by=updated_user,
    )
    return KbSectionOut.model_validate(section, from_attributes=True)


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kb_section_admin_endpoint(
    section_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the section to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a knowledge base section via the admin API."""
    kb_section_service.delete_kb_section(
        db,
        tenant_id=tenant_id,
        section_id=section_id,
        deleted_by=x_user or "anonymous",
    )
    return None


__all__ = [
    "list_kb_sections_admin_endpoint",
    "create_kb_section_admin_endpoint",
    "get_kb_section_admin_endpoint",
    "update_kb_section_admin_endpoint",
    "delete_kb_section_admin_endpoint",
]