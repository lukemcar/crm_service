"""
Service layer for TicketAudit entities.

This module implements list operations for ticket audit events and
optionally provides a create function for internal use.  Audit
events are append‑only and represent discrete changes to a ticket's
state.  Service functions enforce tenant scoping and emit
appropriate events via the ticket audit producer after successful
commits when creating audit entries.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status  # noqa: F401
from sqlalchemy.orm import Session

from app.domain.models.ticket_audit import TicketAudit
from app.messaging.producers.ticket_audit_producer import (
    TicketAuditMessageProducer as AuditProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("ticket_audit_service")


def _snapshot(audit: TicketAudit) -> Dict[str, Any]:
    """Return a dictionary representation of a TicketAudit for event payloads."""
    return {
        "id": audit.id,
        "tenant_id": audit.tenant_id,
        "ticket_id": audit.ticket_id,
        "event_type": audit.event_type,
        "actor_type": audit.actor_type,
        "actor_contact_id": audit.actor_contact_id,
        "actor_user_id": audit.actor_user_id,
        "actor_display_name": audit.actor_display_name,
        "ai_session_id": audit.ai_session_id,
        "before": audit.before,
        "after": audit.after,
        "occurred_at": audit.occurred_at.isoformat() if audit.occurred_at else None,
    }


def list_ticket_audits(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    event_type: Optional[str] = None,
    actor_type: Optional[str] = None,
) -> List[TicketAudit]:
    """List audit events for a given ticket with optional filters."""
    logger.debug(
        "Listing ticket audits: tenant_id=%s, ticket_id=%s, event_type=%s, actor_type=%s",
        tenant_id,
        ticket_id,
        event_type,
        actor_type,
    )
    query = db.query(TicketAudit).filter(
        TicketAudit.tenant_id == tenant_id,
        TicketAudit.ticket_id == ticket_id,
    )
    if event_type:
        query = query.filter(TicketAudit.event_type == event_type)
    if actor_type:
        query = query.filter(TicketAudit.actor_type == actor_type)
    return query.order_by(TicketAudit.occurred_at.asc()).all()


def create_ticket_audit(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    event_type: str,
    actor_type: str,
    actor_contact_id: Optional[uuid.UUID] = None,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_display_name: Optional[str] = None,
    ai_session_id: Optional[uuid.UUID] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    created_by: str | None = None,
) -> TicketAudit:
    """Create a ticket audit entry and publish a created event.

    This function is intended for internal use by other services when a
    ticket is mutated.  It records the event and emits a corresponding
    audit.created event for downstream consumers.
    """
    logger.debug(
        "Creating ticket audit: tenant_id=%s, ticket_id=%s, event_type=%s, actor_type=%s",
        tenant_id,
        ticket_id,
        event_type,
        actor_type,
    )
    audit = TicketAudit(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_contact_id=actor_contact_id,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        ai_session_id=ai_session_id,
        before=before,
        after=after,
        occurred_at=datetime.utcnow(),
    )
    # Note: TicketAudit has no created_by column; occurred_at is set explicitly.
    db.add(audit)
    commit_or_raise(db, refresh=audit, action="create ticket audit")
    snapshot = _snapshot(audit)
    AuditProducer.send_ticket_audit_created(tenant_id=tenant_id, payload=snapshot)
    return audit