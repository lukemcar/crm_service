"""
Admin FastAPI routes for support macros.

These endpoints allow administrators to manage support macros across
tenants.  Listing supports optional tenant scoping for cross‑tenant
searches.  Create and mutation operations require an explicit
``tenant_id`` in the request body or query parameter to ensure that
the operation applies within the correct tenant.  Audit fields are
populated from the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.support_macro_service import (
    list_support_macros as service_list_support_macros,
    create_support_macro as service_create_support_macro,
    update_support_macro as service_update_support_macro,
    get_support_macro as service_get_support_macro,
    delete_support_macro as service_delete_support_macro,
)
from app.domain.schemas.support_macro import (
    AdminCreateSupportMacro,
    SupportMacroUpdate,
    SupportMacroOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/support_macros",
    tags=["SupportMacros"],
)


@router.get("/", response_model=PaginationEnvelope[SupportMacroOut])
def list_support_macros_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SupportMacroOut]:
    """List or search support macros across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Filters perform exact matches on ``is_active``.  Results are
    ordered by creation date descending and wrapped in a pagination
    envelope.  The total matching count is included.
    """
    macros, total = service_list_support_macros(
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
def create_support_macro_admin(
    *,
    macro_in: AdminCreateSupportMacro,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SupportMacroOut:
    """Create a new support macro on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateSupportMacro``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    macro = service_create_support_macro(
        db,
        tenant_id=macro_in.tenant_id,
        request=macro_in,
        created_by=created_user,
    )
    return SupportMacroOut.model_validate(macro, from_attributes=True)


@router.patch("/{macro_id}", response_model=SupportMacroOut)
def update_support_macro_admin(
    *,
    macro_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the support macro to update"
    ),
    macro_update: SupportMacroUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SupportMacroOut:
    """Apply updates to a support macro as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    macro = service_update_support_macro(
        db,
        tenant_id=tenant_id,
        macro_id=macro_id,
        request=macro_update,
        updated_by=updated_user,
    )
    return SupportMacroOut.model_validate(macro, from_attributes=True)


@router.get("/{macro_id}", response_model=SupportMacroOut)
def get_support_macro_admin(
    *,
    macro_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the support macro to retrieve"
    ),
    db: Session = Depends(get_db),
) -> SupportMacroOut:
    """Retrieve a support macro across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    macro can be resolved in the correct tenant context.  Raises 404
    if the macro does not exist in the tenant.
    """
    macro = service_get_support_macro(
        db, tenant_id=tenant_id, macro_id=macro_id
    )
    return SupportMacroOut.model_validate(macro, from_attributes=True)


@router.delete("/{macro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_support_macro_admin(
    *,
    macro_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the support macro to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a support macro as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_support_macro(
        db, tenant_id=tenant_id, macro_id=macro_id
    )
    return None