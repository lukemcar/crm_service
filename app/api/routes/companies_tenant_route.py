"""
Tenant‑scoped FastAPI routes for companies.

These endpoints allow tenants to list, create, patch, retrieve and delete
companies that belong to them.  Nested resources (phone numbers, emails,
addresses, social profiles, notes, company relationships and company
contacts) are exposed via a separate nested router.  Responses are
wrapped in pagination envelopes where appropriate.  Audit fields are
populated using the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.domain.services.company_service import (
    list_companies as service_list_companies,
    create_company as service_create_company,
    patch_company as service_patch_company,
    get_company as service_get_company,
    delete_company as service_delete_company,
)
from app.domain.schemas.company import (
    TenantCreateCompany,
    CompanyOut,
)
from app.domain.schemas.json_patch import JsonPatchRequest
from app.domain.schemas.common import PaginationEnvelope


from app.core.db import get_db


router = APIRouter(
    prefix="/tenants/{tenant_id}/companies",
    tags=["Companies"],
)


@router.get("/", response_model=PaginationEnvelope[CompanyOut])
def list_companies_endpoint(
    tenant_id: UUID,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    contact_name: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[CompanyOut]:
    """List or search companies for a tenant.

    Filters are optional and perform case‑insensitive substring matches.
    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of companies.
    """
    companies, total = service_list_companies(
        db,
        tenant_id=tenant_id,
        name=name,
        phone=phone,
        email=email,
        contact_name=contact_name,
        limit=limit,
        offset=offset,
    )
    items: List[CompanyOut] = [CompanyOut.model_validate(c, from_attributes=True) for c in companies]
    return PaginationEnvelope[CompanyOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company_endpoint(
    tenant_id: UUID,
    company_in: TenantCreateCompany,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyOut:
    """Create a new company for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the company and nested objects are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    company = service_create_company(
        db,
        tenant_id=tenant_id,
        request=company_in,
        created_by=created_user,
    )
    return CompanyOut.model_validate(company, from_attributes=True)


@router.patch("/{company_id}", response_model=CompanyOut)
def patch_company_endpoint(
    tenant_id: UUID,
    company_id: UUID,
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyOut:
    """Apply a JSON Patch document to a company.

    See RFC 6902 for details on JSON Patch semantics.  Only ``add``,
    ``replace`` and ``remove`` operations are supported.  Relationship
    changes (company relationships and contact relationships) must be
    performed via the dedicated nested endpoints.
    """
    modified_user = x_user or "anonymous"
    company = service_patch_company(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        patch_request=patch_request,
        updated_by=modified_user,
    )
    return CompanyOut.model_validate(company, from_attributes=True)


@router.get("/{company_id}", response_model=CompanyOut)
def get_company_endpoint(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> CompanyOut:
    """Retrieve a single company by ID within a tenant.

    Raises 404 if the company does not exist or does not belong to
    the tenant.
    """
    company = service_get_company(db, tenant_id=tenant_id, company_id=company_id)
    return CompanyOut.model_validate(company, from_attributes=True)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_endpoint(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a company from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the company does
    not exist or does not belong to the tenant.  The optional
    ``X-User`` header is ignored for deletion events; event
    publishers do not include a user field for deletions.
    """
    service_delete_company(db, tenant_id=tenant_id, company_id=company_id)
    return None