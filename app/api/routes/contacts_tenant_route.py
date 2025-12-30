"""
Tenant‑scoped FastAPI routes for contacts.

These endpoints allow tenants to create, retrieve, patch and delete
contacts within their scope.  Nested resources are exposed via a
separate router (see ``contacts_tenant_nested_routes.py``).  Query
parameters provide filtering and pagination capabilities.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from contact_service import (
    list_contacts as service_list_contacts,
    get_contact as service_get_contact,
    create_contact as service_create_contact,
    patch_contact as service_patch_contact,
    delete_contact as service_delete_contact,
)
from pydantic.contact_models import (
    TenantCreateContact,
    ContactOut,
    ContactSearchCriteria,
)
from json_patch import JsonPatchRequest
from common import PaginationEnvelope

try:
    from app.api.deps import get_db  # type: ignore
except ImportError:
    def get_db():  # pragma: no cover
        raise HTTPException(status_code=500, detail="Database dependency not configured")


router = APIRouter(prefix="/tenants/{tenant_id}/contacts", tags=["Contacts"])


@router.get("/", response_model=PaginationEnvelope[ContactOut])
def list_contacts_endpoint(
    tenant_id: UUID,
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """List or search contacts for a tenant.

    Returns a paginated list of contacts matching the optional search
    criteria.  Results are wrapped in a pagination envelope.
    """
    contacts, total = service_list_contacts(
        db,
        tenant_id=tenant_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        company_name=company_name,
        limit=limit,
        offset=offset,
    )
    items: List[ContactOut] = [ContactOut.model_validate(c, from_attributes=True) for c in contacts]
    return PaginationEnvelope[ContactOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact_endpoint(
    tenant_id: UUID,
    contact_in: TenantCreateContact,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    """Create a new contact for the tenant."""
    created_user = x_user or "anonymous"
    contact = service_create_contact(
        db,
        tenant_id=tenant_id,
        request=contact_in,
        created_by=created_user,
    )
    return ContactOut.model_validate(contact, from_attributes=True)


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact_endpoint(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a contact by ID within the tenant."""
    contact = service_get_contact(db, tenant_id=tenant_id, contact_id=contact_id)
    return ContactOut.model_validate(contact, from_attributes=True)


@router.patch("/{contact_id}", response_model=ContactOut)
def patch_contact_endpoint(
    tenant_id: UUID,
    contact_id: UUID,
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    """Apply JSON Patch to a contact."""
    updated_user = x_user or "anonymous"
    contact = service_patch_contact(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        patch_request=patch_request,
        updated_by=updated_user,
    )
    return ContactOut.model_validate(contact, from_attributes=True)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_endpoint(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a contact for the tenant."""
    service_delete_contact(db, tenant_id=tenant_id, contact_id=contact_id)
    return None
