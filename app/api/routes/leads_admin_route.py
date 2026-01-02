"""
Admin FastAPI routes for leads.

These endpoints allow administrators to manage leads across tenants.  The
list endpoint supports optional tenant scoping for cross‑tenant search,
whereas create, update, patch and delete operations require an explicit
``tenant_id`` query parameter.  All auditing uses the ``X-User``
header, defaulting to ``"anonymous"`` when not provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import app.domain.services.lead_service as lead_service

from app.domain.schemas.lead import CreateLead, UpdateLead, LeadOut
from app.domain.schemas.json_patch import JsonPatchRequest
from app.domain.schemas.common import PaginationEnvelope

from app.core.db import get_db


router = APIRouter(
    prefix="/admin/leads",
    tags=["Leads"],
)


@router.get("/", response_model=PaginationEnvelope[LeadOut])
def list_leads_admin(
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope results to a single tenant",
    ),
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List or search leads across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Filters
    perform case‑insensitive substring matches.  Results are ordered by
    creation date descending and wrapped in a pagination envelope.
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
def create_lead_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID for the new lead"),
    lead_in: CreateLead,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
):
    """Create a new lead for the specified tenant.

    The tenant ID must be supplied as a query parameter.  The caller's
    identity is taken from ``X-User`` header and used for auditing.
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
def update_lead_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the lead to update"),
    lead_id: UUID,
    lead_in: UpdateLead,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
):
    """Replace an existing lead for the given tenant.

    All fields in the request body replace the current values on the lead.
    Missing fields are set to ``null``.
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
def patch_lead_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the lead to patch"),
    lead_id: UUID,
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
):
    """Apply a JSON Patch document to a lead for the given tenant.

    See RFC 6902 for patch semantics.  Only ``add``, ``replace`` and
    ``remove`` operations are supported.
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
def delete_lead_admin(
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the lead to delete"),
    lead_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a lead belonging to the given tenant.

    Returns HTTP 204 on success.  Raises 404 if the lead is not found
    or does not belong to the tenant.
    """
    lead_service.service_delete_lead(db, tenant_id=tenant_id, lead_id=lead_id)
    return None
