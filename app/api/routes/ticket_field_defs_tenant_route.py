"""
Tenant‑scoped FastAPI routes for ticket field definitions.

These endpoints allow tenants to list, create, update, retrieve and
delete custom ticket field definitions that belong to them.  Filters
are provided for field type and active status.  Audit fields are
populated from the ``X-User`` header when provided; otherwise
"anonymous" is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
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
    TenantCreateTicketFieldDef,
    TicketFieldDefUpdate,
    TicketFieldDefOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/ticket_field_defs",
    tags=["TicketFieldDefs"],
)


@router.get("/", response_model=PaginationEnvelope[TicketFieldDefOut])
def list_ticket_field_defs_endpoint(
    tenant_id: UUID,
    field_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketFieldDefOut]:
    """List ticket field definitions for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of definitions.
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
def create_ticket_field_def_endpoint(
    tenant_id: UUID,
    field_def_in: TenantCreateTicketFieldDef,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFieldDefOut:
    """Create a new ticket field definition for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the definition are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    defn = service_create_ticket_field_def(
        db,
        tenant_id=tenant_id,
        request=field_def_in,
        created_by=created_user,
    )
    return TicketFieldDefOut.model_validate(defn, from_attributes=True)


@router.patch("/{field_def_id}", response_model=TicketFieldDefOut)
def update_ticket_field_def_endpoint(
    tenant_id: UUID,
    field_def_id: UUID,
    field_def_update: TicketFieldDefUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFieldDefOut:
    """Update an existing ticket field definition.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
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
def get_ticket_field_def_endpoint(
    tenant_id: UUID,
    field_def_id: UUID,
    db: Session = Depends(get_db),
) -> TicketFieldDefOut:
    """Retrieve a single ticket field definition by ID within a tenant.

    Raises 404 if the definition does not exist or does not belong to
    the tenant.
    """
    defn = service_get_ticket_field_def(
        db, tenant_id=tenant_id, field_def_id=field_def_id
    )
    return TicketFieldDefOut.model_validate(defn, from_attributes=True)


@router.delete("/{field_def_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_field_def_endpoint(
    tenant_id: UUID,
    field_def_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket field definition from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the definition does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events; event publishers
    do not include user information for deletions.
    """
    service_delete_ticket_field_def(
        db, tenant_id=tenant_id, field_def_id=field_def_id
    )
    return None