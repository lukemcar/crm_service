"""
Tenant‑scoped nested endpoint for ticket SLA state.

This router exposes read‑only access to a ticket's SLA state within a
tenant.  A ticket SLA state records computed deadlines and breach
flags for a ticket under an SLA policy.  Tenants cannot directly
modify SLA state via this endpoint; state is updated by internal
orchestration processes via the admin API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_sla_state_service import (
    list_ticket_sla_states as service_list_ticket_sla_states,
)
from app.domain.schemas.ticket_sla_state import TicketSlaStateOut


router = APIRouter(
    prefix="/tenants/{tenant_id}/tickets/{ticket_id}/sla_state",
    tags=["Ticket SLA State"],
)


@router.get("/", response_model=TicketSlaStateOut)
def get_ticket_sla_state_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    db: Session = Depends(get_db),
) -> TicketSlaStateOut:
    """Retrieve the SLA state for a specific ticket.

    Returns 404 if no SLA state exists for the ticket.  SLA state
    records are created and updated by internal orchestration and SLA
    computation processes.
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
        from fastapi import HTTPException, status  # local import to avoid circular
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket SLA state not found",
        )
    state = states[0]
    return TicketSlaStateOut.model_validate(state, from_attributes=True)
