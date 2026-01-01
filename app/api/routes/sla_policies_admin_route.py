"""
Admin FastAPI routes for SLA policies.

These endpoints allow administrators to list, create, update, retrieve
and delete SLA policies across tenants.  Listing supports optional
tenant scoping for cross‑tenant searches.  Create and mutation
operations require an explicit ``tenant_id`` in the request body or
query parameter to ensure that the operation applies within the
correct tenant.  Audit fields are populated from the ``X-User``
header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.sla_policy_service import (
    list_sla_policies as service_list_sla_policies,
    create_sla_policy as service_create_sla_policy,
    update_sla_policy as service_update_sla_policy,
    get_sla_policy as service_get_sla_policy,
    delete_sla_policy as service_delete_sla_policy,
)
from app.domain.schemas.sla_policy import (
    AdminCreateSlaPolicy,
    SlaPolicyUpdate,
    SlaPolicyOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/sla_policies",
    tags=["SlaPolicies"],
)


@router.get("/", response_model=PaginationEnvelope[SlaPolicyOut])
def list_sla_policies_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SlaPolicyOut]:
    """List or search SLA policies across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``is_active`` filters policies by activation status.  Results are
    ordered by creation date descending and wrapped in a pagination
    envelope.  The total matching count is included.
    """
    policies, total = service_list_sla_policies(
        db,
        tenant_id=tenant_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items: List[SlaPolicyOut] = [
        SlaPolicyOut.model_validate(p, from_attributes=True) for p in policies
    ]
    return PaginationEnvelope[SlaPolicyOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=SlaPolicyOut, status_code=status.HTTP_201_CREATED)
def create_sla_policy_admin(
    *,
    policy_in: AdminCreateSlaPolicy,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> SlaPolicyOut:
    """Create a new SLA policy on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateSlaPolicy``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    policy = service_create_sla_policy(
        db,
        tenant_id=policy_in.tenant_id,
        request=policy_in,
        created_by=created_user,
    )
    return SlaPolicyOut.model_validate(policy, from_attributes=True)


@router.patch("/{policy_id}", response_model=SlaPolicyOut)
def update_sla_policy_admin(
    *,
    policy_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the SLA policy to update"
    ),
    policy_update: SlaPolicyUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> SlaPolicyOut:
    """Apply updates to an SLA policy as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    policy = service_update_sla_policy(
        db,
        tenant_id=tenant_id,
        policy_id=policy_id,
        request=policy_update,
        updated_by=updated_user,
    )
    return SlaPolicyOut.model_validate(policy, from_attributes=True)


@router.get("/{policy_id}", response_model=SlaPolicyOut)
def get_sla_policy_admin(
    *,
    policy_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the SLA policy to retrieve"
    ),
    db: Session = Depends(get_db),
) -> SlaPolicyOut:
    """Retrieve an SLA policy across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    policy can be resolved in the correct tenant context.  Raises 404
    if the policy does not exist in the tenant.
    """
    policy = service_get_sla_policy(db, tenant_id=tenant_id, policy_id=policy_id)
    return SlaPolicyOut.model_validate(policy, from_attributes=True)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sla_policy_admin(
    *,
    policy_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the SLA policy to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete an SLA policy as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_sla_policy(db, tenant_id=tenant_id, policy_id=policy_id)
    return None
