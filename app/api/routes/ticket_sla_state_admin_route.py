"""
Admin‑scoped nested endpoint for ticket SLA state.

This router exposes read and update operations on ticket SLA state in
the admin context.  SLA state records computed deadlines and breach
flags for a ticket under an SLA policy.  Admins must specify the
tenant_id via a query parameter to ensure correct scoping.  Update
operations require a request body describing the new state values and
use the ``X-User`` header for audit attribution.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_sla_state_service import (
    list_ticket_sla_states as service_list_ticket_sla_states,
    update_ticket_sla_state as service_update_ticket_sla_state,
)
from app.domain.schemas.ticket_sla_state import (
    TicketSlaStateUpdate,
    TicketSlaStateOut,
)


router = APIRouter(
    prefix="/admin/tickets/{ticket_id}/sla_state",
    tags=["Ticket SLA State"],
)


@router.get("/", response_model=TicketSlaStateOut)
def get_ticket_sla_state_admin(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to retrieve SLA state for"
    ),
    db: Session = Depends(get_db),
) -> TicketSlaStateOut:
    """Retrieve the SLA state for a ticket in an admin context.

    Requires an explicit ``tenant_id`` query parameter to scope the lookup.
    Returns 404 if no SLA state exists for the ticket.
    """
    states, _total = service_list_ticket_sla_states(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        sla_policy_id=None,
        limit=1,
        offset=0,
    )
    if not states:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket SLA state not found",
        )
    state = states[0]
    return TicketSlaStateOut.model_validate(state, from_attributes=True)


@router.put("/", response_model=TicketSlaStateOut)
def update_ticket_sla_state_admin(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket whose SLA state will be updated"
    ),
    state_update: TicketSlaStateUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Header(None, alias="X-User"),
) -> TicketSlaStateOut:
    """Update the SLA state for a ticket via the admin API.

    The ``X-User`` header is used for audit purposes; if omitted,
    ``updated_by`` is set to ``"anonymous"``.  Fields omitted in the
    request are left unchanged.
    """
    updated_user = x_user or "anonymous"
    state = service_update_ticket_sla_state(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=state_update,
        updated_by=updated_user,
    )
    return TicketSlaStateOut.model_validate(state, from_attributes=True)
