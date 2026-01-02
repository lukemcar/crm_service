"""
Tenant‑scoped FastAPI routes for support macros.

These endpoints allow tenants to manage support macros that define
pre‑configured actions for updating tickets.  Agents can create,
update, retrieve, list and delete macros within their tenant
context.  Audit fields are populated using the ``X-User`` header
when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services import support_macro_service
from app.domain.schemas.support_macro import (
    TenantCreateSupportMacro,
    SupportMacroUpdate,
    SupportMacroOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/support_macros",
    tags=["SupportMacros"],
)


@router.get("/", response_model=PaginationEnvelope[SupportMacroOut])
def list_support_macros_endpoint(
    tenant_id: UUID,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SupportMacroOut]:
    """List support macros for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of macros.
    """
    macros, total = support_macro_service.list_support_macros(
        db,
        tenant_id=tenant_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items: List[SupportMacroOut] = [
        SupportMacroOut.model_validate(m, from_attributes=True) for m in macros
    ]
    return PaginationEnvelope[SupportMacroOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=SupportMacroOut, status_code=status.HTTP_201_CREATED)
def create_support_macro_endpoint(
    tenant_id: UUID,
    macro_in: TenantCreateSupportMacro,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SupportMacroOut:
    """Create a new support macro for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the macro are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    macro = support_macro_service.create_support_macro(
        db,
        tenant_id=tenant_id,
        request=macro_in,
        created_by=created_user,
    )
    return SupportMacroOut.model_validate(macro, from_attributes=True)


@router.patch("/{macro_id}", response_model=SupportMacroOut)
def update_support_macro_endpoint(
    tenant_id: UUID,
    macro_id: UUID,
    macro_update: SupportMacroUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SupportMacroOut:
    """Update an existing support macro.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    macro = support_macro_service.update_support_macro(
        db,
        tenant_id=tenant_id,
        macro_id=macro_id,
        request=macro_update,
        updated_by=updated_user,
    )
    return SupportMacroOut.model_validate(macro, from_attributes=True)


@router.get("/{macro_id}", response_model=SupportMacroOut)
def get_support_macro_endpoint(
    tenant_id: UUID,
    macro_id: UUID,
    db: Session = Depends(get_db),
) -> SupportMacroOut:
    """Retrieve a single support macro by ID within a tenant.

    Raises 404 if the macro does not exist or does not belong to
    the tenant.
    """
    macro = support_macro_service.get_support_macro(
        db, tenant_id=tenant_id, macro_id=macro_id
    )
    return SupportMacroOut.model_validate(macro, from_attributes=True)


@router.delete("/{macro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_support_macro_endpoint(
    tenant_id: UUID,
    macro_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a support macro from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the macro does not
    exist or does not belong to the tenant.  The ``X-User`` header is
    currently ignored for deletion events; event publishers do not
    include user information for deletions.
    """
    support_macro_service.delete_support_macro(
        db, tenant_id=tenant_id, macro_id=macro_id
    )
    return None