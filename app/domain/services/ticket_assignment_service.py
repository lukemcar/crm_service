"""
Service layer for TicketAssignment entities.

This module implements list and create operations for ticket
assignments.  Assignment history is append‑only; there is no
update or delete operation.  Service functions enforce tenant
scoping and emit appropriate events via the ticket assignment
producer after successful commits.  Unique and referential
constraints are enforced at the database layer; violations will
surface as integrity errors via ``commit_or_raise``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status  # noqa: F401
from sqlalchemy.orm import Session

from app.domain.models.ticket_assignment import TicketAssignment
from app.domain.schemas.ticket_assignment import (
    TenantCreateTicketAssignment,
    AdminCreateTicketAssignment,
)
from app.messaging.producers.ticket_assignment_producer import (
    TicketAssignmentMessageProducer as AssignmentProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_assignment_service")


def _snapshot(assignment: TicketAssignment) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketAssignment for event payloads."""
    return {
        "id": assignment.id,
        "tenant_id": assignment.tenant_id,
        "ticket_id": assignment.ticket_id,
        "assigned_group_id": assignment.assigned_group_id,
        "assigned_user_id": assignment.assigned_user_id,
        "assigned_by_user_id": assignment.assigned_by_user_id,
        "assigned_by_reason": assignment.assigned_by_reason,
        "ai_session_id": assignment.ai_session_id,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "created_by": assignment.created_by,
    }


def list_ticket_assignments(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
) -> List[TicketAssignment]:
    """List assignment history for a given ticket."""
    logger.debug(
        "Listing ticket assignments: tenant_id=%s, ticket_id=%s",
        tenant_id,
        ticket_id,
    )
    query = db.query(TicketAssignment).filter(
        TicketAssignment.tenant_id == tenant_id,
        TicketAssignment.ticket_id == ticket_id,
    )
    return query.order_by(TicketAssignment.created_at.asc()).all()


def create_ticket_assignment(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateTicketAssignment | AdminCreateTicketAssignment,
    created_by: str,
) -> TicketAssignment:
    """Create a ticket assignment and publish a created event."""
    logger.debug(
        "Creating ticket assignment: tenant_id=%s, ticket_id=%s, assigned_group_id=%s, assigned_user_id=%s",
        tenant_id,
        ticket_id,
        getattr(request, "assigned_group_id", None),
        getattr(request, "assigned_user_id", None),
    )
    assignment = TicketAssignment(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        assigned_group_id=getattr(request, "assigned_group_id", None),
        assigned_user_id=getattr(request, "assigned_user_id", None),
        assigned_by_user_id=getattr(request, "assigned_by_user_id", None),
        assigned_by_reason=getattr(request, "assigned_by_reason", None),
        ai_session_id=getattr(request, "ai_session_id", None),
        created_by=created_by,
    )
    db.add(assignment)
    commit_or_raise(db, refresh=assignment, action="create ticket assignment")
    snapshot = _snapshot(assignment)
    AssignmentProducer.send_ticket_assignment_created(tenant_id=tenant_id, payload=snapshot)
    return assignment


def get_ticket_assignment(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> TicketAssignment:
    """Retrieve a single ticket assignment by ID within a tenant and ticket context."""
    assignment = (
        db.query(TicketAssignment)
        .filter(
            TicketAssignment.id == assignment_id,
            TicketAssignment.tenant_id == tenant_id,
            TicketAssignment.ticket_id == ticket_id,
        )
        .first()
    )
    if not assignment:
        logger.info(
            "Ticket assignment not found: tenant_id=%s, ticket_id=%s, assignment_id=%s",
            tenant_id,
            ticket_id,
            assignment_id,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket assignment not found")
    return assignment