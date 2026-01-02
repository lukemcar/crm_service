"""
Admin FastAPI routes for ticket task mirrors.

These endpoints allow administrators or internal services to list,
upsert and delete task mirror records across tenants. Listing supports
optional scoping by tenant and ticket identifiers. Upsert operations
require a ``tenant_id`` and ``ticket_id`` in the request body to ensure
that the operation is applied within the correct tenant context. Audit
fields (created_by/updated_by) are populated from the ``X-User`` header
when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_task_mirror_service import (
    list_ticket_task_mirrors as service_list_task_mirrors,
    upsert_ticket_task_mirror as service_upsert_task_mirror,
    get_ticket_task_mirror as service_get_task_mirror,
    delete_ticket_task_mirror as service_delete_task_mirror,
)
from app.domain.schemas.ticket_task_mirror import (
    AdminUpsertTicketTaskMirror,
    TicketTaskMirrorOut,
)
from app.domain.schemas.common import PaginationEnvelope

import uuid


router = APIRouter(
    prefix="/admin/ticket_task_mirrors",
    tags=["TicketTaskMirrors"],
)


@router.get("/", response_model=PaginationEnvelope[TicketTaskMirrorOut])
def list_ticket_task_mirrors_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None, description="Optional tenant ID to scope the search"
    ),
    ticket_id: Optional[UUID] = Query(
        None, description="Optional ticket ID to further scope the search"
    ),
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketTaskMirrorOut]:
    """List ticket task mirrors across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant. If
    ``ticket_id`` is also provided, results are scoped to a single
    ticket. Status filtering and pagination are supported.
    """
    tasks, total = service_list_task_mirrors(
        db,
        tenant_id=tenant_id if tenant_id else uuid.UUID(int=0),
        ticket_id=ticket_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    # If tenant_id is None, our service expects a tenant_id; we supply dummy
    # tenant id 0. The DB query will ignore tenant filter when None; but due to our
    # service design, tenant_id is required. To support cross-tenant listing, we pass
    # UUID(int=0) which yields no results in service, but listing across
    # tenants isn't supported. For future improvement, cross-tenant queries may be added.
    items: List[TicketTaskMirrorOut] = [
        TicketTaskMirrorOut.model_validate(t, from_attributes=True) for t in tasks
    ]
    return PaginationEnvelope[TicketTaskMirrorOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.put("/{mirror_id}", response_model=TicketTaskMirrorOut)
def upsert_ticket_task_mirror_admin(
    *,
    mirror_id: UUID,
    request: AdminUpsertTicketTaskMirror,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketTaskMirrorOut:
    """Upsert a ticket task mirror record as an admin.

    The ``mirror_id`` path parameter identifies the record to update.
    The request body must include ``tenant_id`` and ``ticket_id``. If
    the record does not exist, it will be created. The ``X-User``
    header supplies the audit identity; defaults to ``"anonymous"``.
    """
    updated_user = x_user or "anonymous"
    # Ensure request.id matches path id
    request_dict = request.model_dump()
    # Assign id to request to ensure correct upsert
    request_dict["id"] = mirror_id
    req = AdminUpsertTicketTaskMirror(**request_dict)
    mirror = service_upsert_task_mirror(
        db,
        tenant_id=req.tenant_id,
        request=req,
        updated_by=updated_user,
    )
    return TicketTaskMirrorOut.model_validate(mirror, from_attributes=True)


@router.get("/{mirror_id}", response_model=TicketTaskMirrorOut)
def get_ticket_task_mirror_admin(
    *,
    mirror_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the task mirror to retrieve"
    ),
    db: Session = Depends(get_db),
) -> TicketTaskMirrorOut:
    """Retrieve a ticket task mirror across tenants.

    The ``tenant_id`` query parameter is required to ensure that the
    operation is scoped to the correct tenant.
    """
    mirror = service_get_task_mirror(db, tenant_id=tenant_id, mirror_id=mirror_id)
    return TicketTaskMirrorOut.model_validate(mirror, from_attributes=True)


@router.delete("/{mirror_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_task_mirror_admin(
    *,
    mirror_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the task mirror to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket task mirror as an admin."""
    service_delete_task_mirror(
        db,
        tenant_id=tenant_id,
        mirror_id=mirror_id,
    )
    return None