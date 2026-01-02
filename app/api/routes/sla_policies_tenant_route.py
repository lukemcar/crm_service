"""
Tenant‑scoped FastAPI routes for SLA policies.

These endpoints allow tenants to list, create, update, retrieve and
delete SLA policies that belong to them.  A filter is provided for
active status.  Audit fields are populated from the ``X-User``
header when provided; otherwise "anonymous" is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
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
    TenantCreateSlaPolicy,
    SlaPolicyUpdate,
    SlaPolicyOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/sla_policies",
    tags=["SlaPolicies"],
)


@router.get("/", response_model=PaginationEnvelope[SlaPolicyOut])
def list_sla_policies_endpoint(
    tenant_id: UUID,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SlaPolicyOut]:
    """List SLA policies for a tenant with an optional active filter.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of policies.
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
def create_sla_policy_endpoint(
    tenant_id: UUID,
    policy_in: TenantCreateSlaPolicy,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SlaPolicyOut:
    """Create a new SLA policy for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the policy are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    policy = service_create_sla_policy(
        db,
        tenant_id=tenant_id,
        request=policy_in,
        created_by=created_user,
    )
    return SlaPolicyOut.model_validate(policy, from_attributes=True)


@router.patch("/{policy_id}", response_model=SlaPolicyOut)
def update_sla_policy_endpoint(
    tenant_id: UUID,
    policy_id: UUID,
    policy_update: SlaPolicyUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SlaPolicyOut:
    """Update an existing SLA policy.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
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
def get_sla_policy_endpoint(
    tenant_id: UUID,
    policy_id: UUID,
    db: Session = Depends(get_db),
) -> SlaPolicyOut:
    """Retrieve a single SLA policy by ID within a tenant.

    Raises 404 if the policy does not exist or does not belong to
    the tenant.
    """
    policy = service_get_sla_policy(db, tenant_id=tenant_id, policy_id=policy_id)
    return SlaPolicyOut.model_validate(policy, from_attributes=True)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sla_policy_endpoint(
    tenant_id: UUID,
    policy_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an SLA policy from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the policy does
    not exist or does not belong to the tenant.
    The ``X-User`` header is currently ignored for deletion events;
    event publishers do not include user information for deletions.
    """
    service_delete_sla_policy(db, tenant_id=tenant_id, policy_id=policy_id)
    return None
