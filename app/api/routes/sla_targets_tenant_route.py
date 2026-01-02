"""
Tenant‑scoped FastAPI routes for SLA targets.

These endpoints allow tenants to list, create, update, retrieve and
delete SLA targets that belong to them.  Targets define response and
resolution time thresholds for tickets of a given priority under a
specific SLA policy.  Filters are provided for policy and priority.
Audit fields are populated from the ``X-User`` header when provided;
otherwise "anonymous" is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.sla_target_service import (
    list_sla_targets as service_list_sla_targets,
    create_sla_target as service_create_sla_target,
    update_sla_target as service_update_sla_target,
    get_sla_target as service_get_sla_target,
    delete_sla_target as service_delete_sla_target,
)
from app.domain.schemas.sla_target import (
    TenantCreateSlaTarget,
    SlaTargetUpdate,
    SlaTargetOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/sla_targets",
    tags=["SlaTargets"],
)


@router.get("/", response_model=PaginationEnvelope[SlaTargetOut])
def list_sla_targets_endpoint(
    tenant_id: UUID,
    sla_policy_id: Optional[UUID] = None,
    priority: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SlaTargetOut]:
    """List SLA targets for a tenant with optional policy and priority filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of targets.
    """
    targets, total = service_list_sla_targets(
        db,
        tenant_id=tenant_id,
        sla_policy_id=sla_policy_id,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    items: List[SlaTargetOut] = [
        SlaTargetOut.model_validate(t, from_attributes=True) for t in targets
    ]
    return PaginationEnvelope[SlaTargetOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=SlaTargetOut, status_code=status.HTTP_201_CREATED)
def create_sla_target_endpoint(
    tenant_id: UUID,
    target_in: TenantCreateSlaTarget,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SlaTargetOut:
    """Create a new SLA target for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` is set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    target = service_create_sla_target(
        db,
        tenant_id=tenant_id,
        request=target_in,
        created_by=created_user,
    )
    return SlaTargetOut.model_validate(target, from_attributes=True)


@router.patch("/{target_id}", response_model=SlaTargetOut)
def update_sla_target_endpoint(
    tenant_id: UUID,
    target_id: UUID,
    target_update: SlaTargetUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SlaTargetOut:
    """Update an existing SLA target.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    target = service_update_sla_target(
        db,
        tenant_id=tenant_id,
        target_id=target_id,
        request=target_update,
        updated_by=updated_user,
    )
    return SlaTargetOut.model_validate(target, from_attributes=True)


@router.get("/{target_id}", response_model=SlaTargetOut)
def get_sla_target_endpoint(
    tenant_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
) -> SlaTargetOut:
    """Retrieve a single SLA target by ID within a tenant.

    Raises 404 if the target does not exist or does not belong to
    the tenant.
    """
    target = service_get_sla_target(
        db, tenant_id=tenant_id, target_id=target_id
    )
    return SlaTargetOut.model_validate(target, from_attributes=True)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sla_target_endpoint(
    tenant_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an SLA target from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the target does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events.
    """
    service_delete_sla_target(
        db, tenant_id=tenant_id, target_id=target_id
    )
    return None
