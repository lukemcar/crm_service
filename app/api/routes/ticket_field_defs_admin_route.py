"""
Admin FastAPI routes for ticket field definitions.

These endpoints allow administrators to list, create, update, retrieve
and delete ticket field definitions across tenants.  Listing supports
optional tenant scoping to a single tenant.  Create and mutation
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
from app.domain.services.ticket_field_def_service import (
    list_ticket_field_defs as service_list_ticket_field_defs,
    create_ticket_field_def as service_create_ticket_field_def,
    update_ticket_field_def as service_update_ticket_field_def,
    get_ticket_field_def as service_get_ticket_field_def,
    delete_ticket_field_def as service_delete_ticket_field_def,
)
from app.domain.schemas.ticket_field_def import (
    AdminCreateTicketFieldDef,
    TicketFieldDefUpdate,
    TicketFieldDefOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/ticket_field_defs",
    tags=["TicketFieldDefs"],
)


@router.get("/", response_model=PaginationEnvelope[TicketFieldDefOut])
def list_ticket_field_defs_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    field_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketFieldDefOut]:
    """List or search ticket field definitions across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    The ``field_type`` and ``is_active`` filters perform exact matches
    on the respective fields.  Results are ordered by creation date
    descending and wrapped in a pagination envelope.  The total
    matching count is included.
    """
    defs, total = service_list_ticket_field_defs(
        db,
        tenant_id=tenant_id,
        field_type=field_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items: List[TicketFieldDefOut] = [
        TicketFieldDefOut.model_validate(d, from_attributes=True) for d in defs
    ]
    return PaginationEnvelope[TicketFieldDefOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=TicketFieldDefOut, status_code=status.HTTP_201_CREATED)
def create_ticket_field_def_admin(
    *,
    field_def_in: AdminCreateTicketFieldDef,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFieldDefOut:
    """Create a new ticket field definition on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateTicketFieldDef``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    defn = service_create_ticket_field_def(
        db,
        tenant_id=field_def_in.tenant_id,
        request=field_def_in,
        created_by=created_user,
    )
    return TicketFieldDefOut.model_validate(defn, from_attributes=True)


@router.patch("/{field_def_id}", response_model=TicketFieldDefOut)
def update_ticket_field_def_admin(
    *,
    field_def_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket field definition to update"
    ),
    field_def_update: TicketFieldDefUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFieldDefOut:
    """Apply updates to a ticket field definition as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    defn = service_update_ticket_field_def(
        db,
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        request=field_def_update,
        updated_by=updated_user,
    )
    return TicketFieldDefOut.model_validate(defn, from_attributes=True)


@router.get("/{field_def_id}", response_model=TicketFieldDefOut)
def get_ticket_field_def_admin(
    *,
    field_def_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket field definition to retrieve"
    ),
    db: Session = Depends(get_db),
) -> TicketFieldDefOut:
    """Retrieve a ticket field definition across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    definition can be resolved in the correct tenant context.  Raises
    404 if the definition does not exist in the tenant.
    """
    defn = service_get_ticket_field_def(
        db, tenant_id=tenant_id, field_def_id=field_def_id
    )
    return TicketFieldDefOut.model_validate(defn, from_attributes=True)


@router.delete("/{field_def_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_field_def_admin(
    *,
    field_def_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket field definition to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket field definition as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_ticket_field_def(
        db, tenant_id=tenant_id, field_def_id=field_def_id
    )
    return None