"""
Admin FastAPI routes for contacts.

These endpoints allow administrators to manage contacts across
tenants.  A tenant identifier is required for mutations and reads
against a specific contact to ensure the contact belongs to the
specified tenant.  The list endpoint supports optional tenant
scoping for cross‑tenant search.  Responses are wrapped in
pagination envelopes where appropriate.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.domain.services.contact_service import (
    list_contacts as service_list_contacts,
    get_contact as service_get_contact,
    create_contact as service_create_contact,
    patch_contact as service_patch_contact,
    delete_contact as service_delete_contact,
)
from app.domain.schemas.contact import AdminCreateContact, ContactOut, ContactSearchCriteria
from app.domain.schemas.json_patch import JsonPatchRequest
from app.domain.schemas.common import PaginationEnvelope

from app.core.db import get_db


router = APIRouter(prefix="/admin/contacts", tags=["Contacts"])


@router.get("/", response_model=PaginationEnvelope[ContactOut])
def list_contacts_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope results to a single tenant",
    ),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> PaginationEnvelope[ContactOut]:
    """List or search contacts across tenants.

    If ``tenant_id`` is provided, the results are scoped to that tenant.
    Filters perform case‑insensitive substring matches.  Results are
    ordered by creation date descending and wrapped in a pagination
    envelope.
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
def create_contact_admin(
    *,
    contact_in: AdminCreateContact,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> ContactOut:
    """Create a new contact for the specified tenant.

    The tenant identifier must be included in the request body via the
    ``AdminCreateContact`` schema.  The caller's identity is taken
    from the ``X-User`` header and recorded for auditing.
    """
    created_user = x_user or "anonymous"
    contact = service_create_contact(
        db,
        tenant_id=contact_in.tenant_id,
        request=contact_in,
        created_by=created_user,
    )
    return ContactOut.model_validate(contact, from_attributes=True)


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact_admin(
    *,
    contact_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the contact to retrieve"
    ),
    db: Session = Depends(get_db),
) -> ContactOut:
    """Retrieve a contact belonging to a given tenant.

    A tenant identifier is required to ensure that the contact ID is
    resolved within the correct tenant scope.
    """
    contact = service_get_contact(db, tenant_id=tenant_id, contact_id=contact_id)
    return ContactOut.model_validate(contact, from_attributes=True)


@router.patch("/{contact_id}", response_model=ContactOut)
def patch_contact_admin(
    *,
    contact_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to patch"),
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> ContactOut:
    """Apply a JSON Patch document to a contact.

    Only ``add``, ``replace`` and ``remove`` operations are supported.
    """
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
def delete_contact_admin(
    *,
    contact_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to delete"),
    db: Session = Depends(get_db),
) -> None:
    """Delete a contact belonging to a given tenant.

    Raises 404 if the contact is not found or does not belong to the
    specified tenant.
    """
    service_delete_contact(db, tenant_id=tenant_id, contact_id=contact_id)
    return None