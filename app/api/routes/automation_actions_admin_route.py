"""
FastAPI router for AutomationAction admin endpoints.

Admin endpoints allow managing automation actions across tenants.  Actions
may be listed, created, updated and deleted via this API.  Collection
endpoints are exposed at ``/admin/automation-actions``.  Mutating
operations require a ``tenant_id`` query parameter to ensure actions are
always scoped correctly.  Audit fields may be captured via headers,
although they are not currently stored.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionUpdate,
    AutomationActionRead,
)
from app.domain.services import automation_action_service


router = APIRouter(prefix="/admin/automation-actions", tags=["automation actions"])


@router.get(
    "/",
    response_model=schemas.PaginationEnvelope[AutomationActionRead],
)
def list_automation_actions(
    *,
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier for scoping; omit to list all tenants"
    ),
    entity_type: Optional[str] = Query(
        None, description="Filter by entity type (e.g., CONTACT, DEAL)"
    ),
    scope_type: Optional[str] = Query(
        None, description="Filter by scope type (RECORD, PIPELINE, PIPELINE_STAGE, LIST)"
    ),
    enabled: Optional[bool] = Query(
        None, description="Filter by enabled state"
    ),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of actions to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of actions to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[AutomationActionRead]:
    """List automation actions (admin context).

    Allows optional filtering by tenant, entity type, scope type and enabled flag.
    Supports pagination via limit and offset.
    """
    if tenant_id is None:
        # Admin must specify a tenant for listing; listing all tenants is not supported yet
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
    items, total = automation_action_service.service_list_actions(
        db,
        tenant_id=tenant_id,
        entity_type=entity_type,
        scope_type=scope_type,
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[AutomationActionRead](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post(
    "/",
    response_model=AutomationActionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_automation_action(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier for the automation action"),
    action_in: AutomationActionCreate,
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> AutomationActionRead:
    """Create a new automation action (admin context)."""
    # Overwrite tenant_id on the body to prevent cross‑tenant associations
    action_data = action_in.model_copy(update={"tenant_id": tenant_id})
    created_by_user: Optional[UUID] = None
    if x_user_id:
        try:
            created_by_user = UUID(x_user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id header")
    action = automation_action_service.service_create_action(
        db,
        tenant_id=tenant_id,
        action_in=action_data,
        created_by_user_id=created_by_user,
    )
    return action


@router.patch(
    "/{action_id}",
    response_model=AutomationActionRead,
)
def update_automation_action(
    *,
    action_id: UUID = Path(..., description="Automation action identifier"),
    tenant_id: UUID = Query(..., description="Tenant identifier for the action"),
    action_in: AutomationActionUpdate,
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> AutomationActionRead:
    """Update an existing automation action (admin context)."""
    updated_by_user: Optional[UUID] = None
    if x_user_id:
        try:
            updated_by_user = UUID(x_user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id header")
    action = automation_action_service.service_update_action(
        db,
        tenant_id=tenant_id,
        action_id=action_id,
        update_in=action_in,
        updated_by_user_id=updated_by_user,
    )
    return action


@router.delete(
    "/{action_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_automation_action(
    *,
    action_id: UUID = Path(..., description="Automation action identifier"),
    tenant_id: UUID = Query(..., description="Tenant identifier for the action"),
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete an automation action (admin context)."""
    deleted_by_user: Optional[UUID] = None
    if x_user_id:
        try:
            deleted_by_user = UUID(x_user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id header")
    automation_action_service.service_delete_action(
        db,
        tenant_id=tenant_id,
        action_id=action_id,
        deleted_by_user_id=deleted_by_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
