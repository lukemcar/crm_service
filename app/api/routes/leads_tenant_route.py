"""
Tenant‑scoped FastAPI routes for leads.

These endpoints allow tenants to list, create, update, patch and delete
leads that belong to them.  Each operation delegates to the service
layer and propagates tenant scoping.  Responses are wrapped in the
pagination envelope model where appropriate.  User identifiers for
auditing are accepted via the ``X-User`` header; if absent a default
value of ``"anonymous"`` is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

import app.domain.services.lead_service as lead_service

from app.domain.schemas.lead import CreateLead, UpdateLead, LeadOut
from app.domain.schemas.json_patch import JsonPatchRequest
from app.domain.schemas.common import PaginationEnvelope

from app.core.db import get_db


router = APIRouter(
    prefix="/tenants/{tenant_id}/leads",
    tags=["Leads"],
)


@router.get("/", response_model=PaginationEnvelope[LeadOut])
def list_leads_endpoint(
    tenant_id: UUID,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List or search leads for a tenant.

    Filters are optional and perform case‑insensitive substring matches.  Results
    are ordered by creation date descending and wrapped in a pagination
    envelope.
    """
    leads, total = lead_service.service_list_leads(
        db,
        tenant_id=tenant_id,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email=email,
        limit=limit,
        offset=offset,
    )
    items: List[LeadOut] = [LeadOut.model_validate(ld, from_attributes=True) for ld in leads]
    return PaginationEnvelope[LeadOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead_endpoint(
    tenant_id: UUID,
    lead_in: CreateLead,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    """Create a new lead for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` are set
    to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    lead = lead_service.service_create_lead(
        db,
        tenant_id=tenant_id,
        lead_in=lead_in,
        created_user=created_user,
    )
    return LeadOut.model_validate(lead, from_attributes=True)


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead_endpoint(
    tenant_id: UUID,
    lead_id: UUID,
    lead_in: UpdateLead,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    """Replace an existing lead.

    All fields in the request body will replace the current values on
    the lead.  Missing fields will be set to ``null``.
    """
    modified_user = x_user or "anonymous"
    lead = lead_service.service_update_lead(
        db,
        tenant_id=tenant_id,
        lead_id=lead_id,
        lead_in=lead_in,
        modified_user=modified_user,
    )
    return LeadOut.model_validate(lead, from_attributes=True)


@router.patch("/{lead_id}", response_model=LeadOut)
def patch_lead_endpoint(
    tenant_id: UUID,
    lead_id: UUID,
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    """Apply a JSON Patch document to a lead.

    See RFC 6902 for details on JSON Patch semantics.  Only ``add``,
    ``replace`` and ``remove`` operations are supported.  Removing a
    required top‑level attribute (e.g. ``first_name``) will result in
    a 400 error.
    """
    modified_user = x_user or "anonymous"
    lead = lead_service.service_patch_lead(
        db,
        tenant_id=tenant_id,
        lead_id=lead_id,
        patch_request=patch_request,
        modified_user=modified_user,
    )
    return LeadOut.model_validate(lead, from_attributes=True)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead_endpoint(
    tenant_id: UUID,
    lead_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a lead from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the lead does not
    exist or does not belong to the tenant.
    """
    lead_service.service_delete_lead(db, tenant_id=tenant_id, lead_id=lead_id)
    # FastAPI will automatically return a 204 response when None is returned
    return None
