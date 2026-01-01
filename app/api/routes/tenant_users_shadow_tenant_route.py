"""
Tenant‑scoped FastAPI routes for tenant user projections.

These endpoints expose the ``tenant_user_shadow`` table as a read‑only
resource.  Clients may list all users for a tenant or retrieve a
specific user by their identifier.  Creation, update and deletion
operations are intentionally not implemented because CRM does not own
these records; they are synchronised from the tenant service.

The route prefix follows the pattern used by other tenant‑scoped
resources: ``/tenants/{tenant_id}/tenant-users``.  Note that the tag
"Tenant Users" is used for grouping in generated OpenAPI docs.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domain.schemas.tenant_user_shadow import TenantUserShadowOut
from app.domain.schemas.common import PaginationEnvelope
from app.domain.services import tenant_user_shadow_service  # noqa: F401
from app.core.db import get_db


router = APIRouter(
    prefix="/tenants/{tenant_id}/tenant-users",
    tags=["Tenant Users"],
)


@router.get("/", response_model=PaginationEnvelope[TenantUserShadowOut])
def list_tenant_users_endpoint(
    tenant_id: UUID,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TenantUserShadowOut]:
    """List or search tenant user projections.

    Filters perform case‑insensitive substring matches on display name
    and email.  Pagination parameters behave consistently with other
    list endpoints.  The total count of matching records is returned
    alongside the items.
    """
    items, total = tenant_user_shadow_service.list_tenant_users(
        db,
        tenant_id=tenant_id,
        display_name=display_name,
        email=email,
        limit=limit,
        offset=offset,
    )
    out_items: List[TenantUserShadowOut] = [
        TenantUserShadowOut.model_validate(u, from_attributes=True) for u in items
    ]
    return PaginationEnvelope[TenantUserShadowOut](
        items=out_items, total=total, limit=limit, offset=offset
    )


@router.get("/{user_id}", response_model=TenantUserShadowOut)
def get_tenant_user_endpoint(
    tenant_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
) -> TenantUserShadowOut:
    """Retrieve a single tenant user projection by identifier.

    Returns HTTP 404 if no matching projection exists for the tenant.
    """
    user = tenant_user_shadow_service.get_tenant_user(
        db, tenant_id=tenant_id, user_id=user_id
    )
    return TenantUserShadowOut.model_validate(user, from_attributes=True)
