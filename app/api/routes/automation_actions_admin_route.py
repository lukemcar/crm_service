"""
Admin FastAPI routes for automation actions.

These endpoints allow administrators to manage automation actions across
tenants.  Listing supports optional tenant scoping for cross‑tenant
searches and filtering by entity_type and scope_type.  Create and
mutation operations require an explicit ``tenant_id`` in the request
body to ensure that the operation applies within the correct tenant.
Audit fields are populated from the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.automation_action_service import (
    list_automation_actions as service_list_actions,
    create_automation_action as service_create_action,
    update_automation_action as service_update_action,
    get_automation_action as service_get_action,
    delete_automation_action as service_delete_action,
)
from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionUpdate,
    AutomationActionRead,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/automation_actions",
    tags=["AutomationActions"],
)


@router.get("/", response_model=PaginationEnvelope[AutomationActionRead])
def list_automation_actions_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    entity_type: Optional[str] = Query(
        None, description="Optional filter by entity_type"
    ),
    scope_type: Optional[str] = Query(
        None, description="Optional filter by scope_type"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[AutomationActionRead]:
    """List or search automation actions across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Filters perform exact matches on ``entity_type`` and ``scope_type``.  Results are
    ordered by creation date descending and wrapped in a pagination envelope.  The
    total matching count is included.
    """
    actions, total = service_list_actions(
        db,
        tenant_id=tenant_id,
        entity_type=entity_type,
        scope_type=scope_type,
        limit=limit,
        offset=offset,
    )
    items: List[AutomationActionRead] = [
        AutomationActionRead.model_validate(a, from_attributes=True) for a in actions
    ]
    return PaginationEnvelope[AutomationActionRead](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=AutomationActionRead, status_code=status.HTTP_201_CREATED)
def create_automation_action_admin(
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID for the automation action to create"
    ),
    action_in: AutomationActionCreate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> AutomationActionRead:
    """Create a new automation action on behalf of a tenant.

    The ``tenant_id`` query parameter is required to ensure that the action is created
    within the correct tenant context.  The ``X-User`` header is used for audit
    purposes; if omitted, audit fields are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    action = service_create_action(
        db,
        tenant_id=tenant_id,
        request=action_in,
        created_by=created_user,
    )
    return AutomationActionRead.model_validate(action, from_attributes=True)


@router.patch("/{action_id}", response_model=AutomationActionRead)
def update_automation_action_admin(
    *,
    action_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the automation action to update"
    ),
    action_update: AutomationActionUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> AutomationActionRead:
    """Apply updates to an automation action as an admin.

    The ``tenant_id`` query parameter is required to ensure that the operation applies within the
    correct tenant.  Only fields provided in the request are updated.
    """
    updated_user = x_user or "anonymous"
    action = service_update_action(
        db,
        tenant_id=tenant_id,
        action_id=action_id,
        request=action_update,
        updated_by=updated_user,
    )
    return AutomationActionRead.model_validate(action, from_attributes=True)


@router.get("/{action_id}", response_model=AutomationActionRead)
def get_automation_action_admin(
    *,
    action_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the automation action to retrieve"
    ),
    db: Session = Depends(get_db),
) -> AutomationActionRead:
    """Retrieve a single automation action across tenants.

    An explicit ``tenant_id`` query parameter is required so that the action can be
    resolved in the correct tenant context.  Raises 404 if the action does not exist
    in the tenant.
    """
    action = service_get_action(db, tenant_id=tenant_id, action_id=action_id)
    return AutomationActionRead.model_validate(action, from_attributes=True)


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation_action_admin(
    *,
    action_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the automation action to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an automation action as an admin.

    The ``tenant_id`` query parameter is required to ensure that the deletion occurs
    within the correct tenant.  Returns HTTP 204 on success.  Event publishers do
    not include user information for deletions.
    """
    service_delete_action(db, tenant_id=tenant_id, action_id=action_id)
    return None


__all__ = ["router"]