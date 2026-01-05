"""
Tenant‑scoped FastAPI routes for automation actions.

These endpoints allow tenants to manage automation actions that define
declarative rules for CRM entities.  Agents can create, update,
retrieve, list and delete automation actions within their tenant
context.  Audit fields are populated using the ``X-User`` header when
provided.
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
    prefix="/tenants/{tenant_id}/automation_actions",
    tags=["AutomationActions"],
)


@router.get("/", response_model=PaginationEnvelope[AutomationActionRead])
def list_automation_actions_endpoint(
    tenant_id: UUID,
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
    """List automation actions for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page results
    accordingly.  The total count of records matching the criteria is
    returned alongside the list of actions.
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
def create_automation_action_endpoint(
    tenant_id: UUID,
    action_in: AutomationActionCreate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> AutomationActionRead:
    """Create a new automation action for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by_user_id`` and ``updated_by_user_id`` fields
    on the action are set to ``"anonymous"``.
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
def update_automation_action_endpoint(
    tenant_id: UUID,
    action_id: UUID,
    action_update: AutomationActionUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> AutomationActionRead:
    """Update an existing automation action.

    The ``X-User`` header supplies the identity of the caller for audit purposes.  Fields
    not provided in the request are left unchanged.
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
def get_automation_action_endpoint(
    tenant_id: UUID,
    action_id: UUID,
    db: Session = Depends(get_db),
) -> AutomationActionRead:
    """Retrieve a single automation action by ID within a tenant.

    Raises 404 if the action does not exist or does not belong to the tenant.
    """
    action = service_get_action(db, tenant_id=tenant_id, action_id=action_id)
    return AutomationActionRead.model_validate(action, from_attributes=True)


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation_action_endpoint(
    tenant_id: UUID,
    action_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete an automation action from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the action does not exist or does
    not belong to the tenant.  The ``X-User`` header is currently ignored for
    deletion events; event publishers do not include user information for deletions.
    """
    service_delete_action(db, tenant_id=tenant_id, action_id=action_id)
    return None


__all__ = ["router"]