"""
Admin FastAPI routes for tickets.

These endpoints allow administrators to list, create, update, retrieve
and delete tickets across tenants.  Listing supports optional tenant
scoping for cross‑tenant searches.  Create and mutation operations
require an explicit ``tenant_id`` in the request body or query
parameter to ensure that the operation applies within the correct
tenant.  Audit fields are populated from the ``X-User`` header when
provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_service import (
    list_tickets as service_list_tickets,
    create_ticket as service_create_ticket,
    update_ticket as service_update_ticket,
    get_ticket as service_get_ticket,
    delete_ticket as service_delete_ticket,
)
from app.domain.schemas.ticket import (
    AdminCreateTicket,
    TicketUpdate,
    TicketOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/tickets",
    tags=["Tickets"],
)


@router.get("/", response_model=PaginationEnvelope[TicketOut])
def list_tickets_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_user_id: Optional[UUID] = None,
    assigned_group_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketOut]:
    """List or search tickets across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    Additional filters perform exact matches on status, priority,
    assigned user and assigned group.  Results are ordered by
    creation date descending and wrapped in a pagination envelope.
    The total matching count is included.
    """
    tickets, total = service_list_tickets(
        db,
        tenant_id=tenant_id,
        status=status,
        priority=priority,
        assigned_user_id=assigned_user_id,
        assigned_group_id=assigned_group_id,
        limit=limit,
        offset=offset,
    )
    items: List[TicketOut] = [TicketOut.model_validate(t, from_attributes=True) for t in tickets]
    return PaginationEnvelope[TicketOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket_admin(
    *,
    ticket_in: AdminCreateTicket,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketOut:
    """Create a new ticket on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateTicket``.  The ``X-User`` header is used for audit
    purposes; if omitted, ``created_by`` and ``updated_by`` are set to
    ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    ticket = service_create_ticket(
        db,
        tenant_id=ticket_in.tenant_id,
        request=ticket_in,
        created_by=created_user,
    )
    return TicketOut.model_validate(ticket, from_attributes=True)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket_admin(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to update"
    ),
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketOut:
    """Apply updates to a ticket as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    ticket = service_update_ticket(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=ticket_update,
        updated_by=updated_user,
    )
    return TicketOut.model_validate(ticket, from_attributes=True)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket_admin(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to retrieve"
    ),
    db: Session = Depends(get_db),
) -> TicketOut:
    """Retrieve a ticket by ID across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    ticket can be resolved in the correct tenant context.  Raises 404
    if the ticket does not exist in the tenant.
    """
    ticket = service_get_ticket(
        db, tenant_id=tenant_id, ticket_id=ticket_id
    )
    return TicketOut.model_validate(ticket, from_attributes=True)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_admin(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a ticket as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_ticket(
        db, tenant_id=tenant_id, ticket_id=ticket_id
    )
    return None
