"""
Admin FastAPI routes for companies.

These endpoints allow administrators to list, create, patch, retrieve and
delete companies across tenants.  Listing supports optional tenant
scoping for cross‑tenant searches.  Create, patch and delete
operations require an explicit ``tenant_id`` query parameter or body
field to ensure that company mutations occur within the correct
tenant.  Audit fields are populated using the ``X-User`` header
when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.domain.services.company_service import (
    list_companies as service_list_companies,
    create_company as service_create_company,
    patch_company as service_patch_company,
    get_company as service_get_company,
    delete_company as service_delete_company,
)
from app.domain.schemas.company import (
    AdminCreateCompany,
    CompanyOut,
)
from app.domain.schemas.json_patch import JsonPatchRequest
from app.domain.schemas.common import PaginationEnvelope

from app.core.db import get_db


router = APIRouter(
    prefix="/admin/companies",
    tags=["Companies"],
)


@router.get("/", response_model=PaginationEnvelope[CompanyOut])
def list_companies_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    contact_name: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[CompanyOut]:
    """List or search companies across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Filters
    perform case‑insensitive substring matches on company name, phone,
    email and contact name.  Results are ordered by creation date
    descending and wrapped in a pagination envelope.  The total
    matching count is included.
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
def create_company_admin(
    *,
    company_in: AdminCreateCompany,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> CompanyOut:
    """Create a new company on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateCompany``.  The ``X-User`` header is used for audit
    purposes; if omitted, ``created_by`` and ``updated_by`` are set to
    ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    company = service_create_company(
        db,
        tenant_id=company_in.tenant_id,
        request=company_in,
        created_by=created_user,
    )
    return CompanyOut.model_validate(company, from_attributes=True)


@router.patch("/{company_id}", response_model=CompanyOut)
def patch_company_admin(
    *,
    company_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to patch"
    ),
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> CompanyOut:
    """Apply a JSON Patch document to a company as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only ``add``, ``replace``
    and ``remove`` operations are supported.  Relationship changes
    must be handled via the nested relationship endpoints.
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
def get_company_admin(
    *,
    company_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to retrieve"
    ),
    db: Session = Depends(get_db),
) -> CompanyOut:
    """Retrieve a company by ID across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    company can be resolved in the correct tenant context.  Raises
    404 if the company does not exist in the tenant.
    """
    company = service_get_company(db, tenant_id=tenant_id, company_id=company_id)
    return CompanyOut.model_validate(company, from_attributes=True)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_admin(
    *,
    company_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a company as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_company(db, tenant_id=tenant_id, company_id=company_id)
    return None