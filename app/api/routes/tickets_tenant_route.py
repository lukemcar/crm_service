"""
Tenant‑scoped FastAPI routes for tickets.

These endpoints allow tenants to list, create, update, retrieve and
delete tickets that belong to them.  Filters are provided for
status, priority and assignee.  Audit fields are populated using
the ``X-User`` header when provided; otherwise "anonymous" is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services import ticket_service  # for mypy namespace support
from app.domain.schemas.ticket import (
    TenantCreateTicket,
    TicketUpdate,
    TicketOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/tickets",
    tags=["Tickets"],
)


@router.get("/", response_model=PaginationEnvelope[TicketOut])
def list_tickets_endpoint(
    tenant_id: UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_user_id: Optional[UUID] = None,
    assigned_group_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketOut]:
    """List tickets for a tenant with optional filters.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of tickets.
    """
    tickets, total = ticket_service.list_tickets(
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
def create_ticket_endpoint(
    tenant_id: UUID,
    ticket_in: TenantCreateTicket,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketOut:
    """Create a new ticket for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the ticket are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    ticket = ticket_service.create_ticket(
        db,
        tenant_id=tenant_id,
        request=ticket_in,
        created_by=created_user,
    )
    return TicketOut.model_validate(ticket, from_attributes=True)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketOut:
    """Update an existing ticket.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    ticket = ticket_service.update_ticket(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=ticket_update,
        updated_by=updated_user,
    )
    return TicketOut.model_validate(ticket, from_attributes=True)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    db: Session = Depends(get_db),
) -> TicketOut:
    """Retrieve a single ticket by ID within a tenant.

    Raises 404 if the ticket does not exist or does not belong to
    the tenant.
    """
    ticket = ticket_service.get_ticket(db, tenant_id=tenant_id, ticket_id=ticket_id)
    return TicketOut.model_validate(ticket, from_attributes=True)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a ticket from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the ticket does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events; event publishers
    do not include user information for deletions.
    """
    ticket_service.delete_ticket(db, tenant_id=tenant_id, ticket_id=ticket_id)
    return None
