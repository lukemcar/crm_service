"""
Tenant‑scoped FastAPI routes for tenant group projections.

These endpoints expose the ``tenant_group_shadow`` table as a read‑only
resource.  Clients may list all groups for a tenant or retrieve a
specific group by its identifier.  No mutation endpoints are defined
because CRM does not own these records; they are managed by the
tenant service and projected into CRM for fast lookup and
referential integrity.

The route prefix is ``/tenants/{tenant_id}/tenant-groups``, matching
other tenant‑scoped resources.  The tag "Tenant Groups" groups these
operations in the generated API documentation.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domain.schemas.tenant_group_shadow import TenantGroupShadowOut
from app.domain.schemas.common import PaginationEnvelope
from app.domain.services import tenant_group_shadow_service  # noqa: F401
from app.core.db import get_db


router = APIRouter(
    prefix="/tenants/{tenant_id}/tenant-groups",
    tags=["Tenant Groups"],
)


@router.get("/", response_model=PaginationEnvelope[TenantGroupShadowOut])
def list_tenant_groups_endpoint(
    tenant_id: UUID,
    name: Optional[str] = None,
    key: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TenantGroupShadowOut]:
    """List or search tenant group projections.

    Filters perform case‑insensitive substring matches on group_name
    and exact matches on group_key.  Pagination semantics mirror
    other list endpoints in the service.
    """
    items, total = tenant_group_shadow_service.list_tenant_groups(
        db,
        tenant_id=tenant_id,
        name=name,
        key=key,
        limit=limit,
        offset=offset,
    )
    out_items: List[TenantGroupShadowOut] = [
        TenantGroupShadowOut.model_validate(g, from_attributes=True) for g in items
    ]
    return PaginationEnvelope[TenantGroupShadowOut](
        items=out_items, total=total, limit=limit, offset=offset
    )


@router.get("/{group_id}", response_model=TenantGroupShadowOut)
def get_tenant_group_endpoint(
    tenant_id: UUID,
    group_id: UUID,
    db: Session = Depends(get_db),
) -> TenantGroupShadowOut:
    """Retrieve a single tenant group projection by identifier.

    Returns HTTP 404 if the projection does not exist for the tenant.
    """
    group = tenant_group_shadow_service.get_tenant_group(
        db,
        tenant_id=tenant_id,
        group_id=group_id,
    )
    return TenantGroupShadowOut.model_validate(group, from_attributes=True)
