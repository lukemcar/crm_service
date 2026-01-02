"""
Admin FastAPI routes for SLA targets.

These endpoints allow administrators to list, create, update, retrieve
and delete SLA targets across tenants.  Listing supports optional
tenant scoping and filtering by policy and priority.  Create and
mutation operations require an explicit ``tenant_id`` in the request
body or query parameter to ensure that the operation applies within
the correct tenant.  Audit fields are populated from the ``X-User``
header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
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
    AdminCreateSlaTarget,
    SlaTargetUpdate,
    SlaTargetOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/sla_targets",
    tags=["SlaTargets"],
)


@router.get("/", response_model=PaginationEnvelope[SlaTargetOut])
def list_sla_targets_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    sla_policy_id: Optional[UUID] = None,
    priority: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[SlaTargetOut]:
    """List or search SLA targets across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    ``sla_policy_id`` filters by policy; ``priority`` filters by
    priority value.  Results are ordered by creation date descending and
    wrapped in a pagination envelope.  The total matching count is
    included.
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
def create_sla_target_admin(
    *,
    target_in: AdminCreateSlaTarget,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SlaTargetOut:
    """Create a new SLA target on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateSlaTarget``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` is set to
    ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    target = service_create_sla_target(
        db,
        tenant_id=target_in.tenant_id,
        request=target_in,
        created_by=created_user,
    )
    return SlaTargetOut.model_validate(target, from_attributes=True)


@router.patch("/{target_id}", response_model=SlaTargetOut)
def update_sla_target_admin(
    *,
    target_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the SLA target to update"
    ),
    target_update: SlaTargetUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> SlaTargetOut:
    """Apply updates to an SLA target as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
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
def get_sla_target_admin(
    *,
    target_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the SLA target to retrieve"
    ),
    db: Session = Depends(get_db),
) -> SlaTargetOut:
    """Retrieve an SLA target across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    target can be resolved in the correct tenant context.  Raises 404
    if the target does not exist in the tenant.
    """
    target = service_get_sla_target(
        db, tenant_id=tenant_id, target_id=target_id
    )
    return SlaTargetOut.model_validate(target, from_attributes=True)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sla_target_admin(
    *,
    target_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the SLA target to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an SLA target as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_sla_target(
        db, tenant_id=tenant_id, target_id=target_id
    )
    return None
