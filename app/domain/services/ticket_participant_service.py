"""
Service layer for TicketParticipant entities.

This module implements list, create and delete operations for ticket
participants.  Participants are append‑only; there is no update
operation.  Service functions enforce tenant scoping and emit
appropriate events via the ticket participant producer after
successful commits.  Unique and check constraints are enforced at
the database layer; violations will raise integrity errors via
``commit_or_raise``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.ticket_participant import TicketParticipant
from app.domain.schemas.ticket_participant import (
    TenantCreateTicketParticipant,
    AdminCreateTicketParticipant,
)
from app.messaging.producers.ticket_participant_producer import (
    TicketParticipantMessageProducer as ParticipantProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_participant_service")


def _snapshot(participant: TicketParticipant) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketParticipant for event payloads."""
    return {
        "id": participant.id,
        "tenant_id": participant.tenant_id,
        "ticket_id": participant.ticket_id,
        "participant_type": participant.participant_type,
        "contact_id": participant.contact_id,
        "user_id": participant.user_id,
        "role": participant.role,
        "created_at": participant.created_at.isoformat() if participant.created_at else None,
        "created_by": participant.created_by,
    }


def list_ticket_participants(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    participant_type: Optional[str] = None,
    role: Optional[str] = None,
) -> List[TicketParticipant]:
    """List ticket participants for a given ticket with optional filters."""
    logger.debug(
        "Listing ticket participants: tenant_id=%s, ticket_id=%s, participant_type=%s, role=%s",
        tenant_id,
        ticket_id,
        participant_type,
        role,
    )
    query = db.query(TicketParticipant).filter(
        TicketParticipant.tenant_id == tenant_id,
        TicketParticipant.ticket_id == ticket_id,
    )
    if participant_type:
        query = query.filter(TicketParticipant.participant_type == participant_type)
    if role:
        query = query.filter(TicketParticipant.role == role)
    return query.order_by(TicketParticipant.created_at.asc()).all()


def create_ticket_participant(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateTicketParticipant | AdminCreateTicketParticipant,
    created_by: str,
) -> TicketParticipant:
    """Create a ticket participant and publish a created event."""
    logger.debug(
        "Creating ticket participant: tenant_id=%s, ticket_id=%s, type=%s",
        tenant_id,
        ticket_id,
        request.participant_type,
    )
    participant = TicketParticipant(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_type=request.participant_type,
        contact_id=request.contact_id,
        user_id=request.user_id,
        role=request.role or "cc",
        created_by=created_by,
    )
    db.add(participant)
    commit_or_raise(db, refresh=participant, action="create ticket participant")
    snapshot = _snapshot(participant)
    ParticipantProducer.send_ticket_participant_created(tenant_id=tenant_id, payload=snapshot)
    return participant


def get_ticket_participant(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    participant_id: uuid.UUID,
) -> TicketParticipant:
    """Retrieve a single ticket participant by ID within a tenant and ticket context."""
    participant = (
        db.query(TicketParticipant)
        .filter(
            TicketParticipant.id == participant_id,
            TicketParticipant.tenant_id == tenant_id,
            TicketParticipant.ticket_id == ticket_id,
        )
        .first()
    )
    if not participant:
        logger.info(
            "Ticket participant not found: tenant_id=%s, ticket_id=%s, participant_id=%s",
            tenant_id,
            ticket_id,
            participant_id,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket participant not found")
    return participant


def delete_ticket_participant(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    participant_id: uuid.UUID,
) -> None:
    """Delete a ticket participant and publish a deletion event."""
    participant = get_ticket_participant(
        db, tenant_id=tenant_id, ticket_id=ticket_id, participant_id=participant_id
    )
    db.delete(participant)
    commit_or_raise(db, action="delete ticket participant")
    # Publish deletion event with timestamp
    ParticipantProducer.send_ticket_participant_deleted(
        tenant_id=tenant_id,
        deleted_dt=datetime.utcnow().isoformat(),
    )
    return None