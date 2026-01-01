"""Service layer for CSAT responses.

This module provides CRUD operations for CSAT responses. Responses
capture satisfaction ratings and comments tied to a specific ticket
and optional survey. Listing operations support filtering by survey
and pagination. Updates and deletes are restricted to administrative
contexts.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.csat_response import CsatResponse
from app.domain.schemas.csat_response import (
    CsatResponseUpdate,
    TenantCreateCsatResponse,
    AdminCreateCsatResponse,
)
from app.domain.schemas.events.csat_response_event import CsatResponseDelta
from app.messaging.producers.csat_response_producer import (
    CsatResponseMessageProducer as CsatResponseProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("csat_response_service")


def _snapshot(resp: CsatResponse) -> Dict[str, Any]:
    """Return a dictionary representation of a CsatResponse suitable for event payloads."""
    return {
        "id": resp.id,
        "tenant_id": resp.tenant_id,
        "csat_survey_id": resp.csat_survey_id,
        "ticket_id": resp.ticket_id,
        "contact_id": resp.contact_id,
        "rating": resp.rating,
        "comment": resp.comment,
        "submitted_at": resp.submitted_at.isoformat() if resp.submitted_at else None,
        "created_at": resp.created_at.isoformat() if resp.created_at else None,
        "created_by": resp.created_by,
    }


def _compute_delta(resp: CsatResponse, updates: Dict[str, Any]) -> CsatResponseDelta:
    """Compute a delta object for modified base fields on a CSAT response."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(resp, field)
        if isinstance(current, datetime):
            current_val = current.isoformat()
        else:
            current_val = current
        new_val = value.isoformat() if isinstance(value, datetime) else value
        if current_val != new_val:
            changed[field] = value
    return CsatResponseDelta(base_fields=changed or None)


def list_csat_responses(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    csat_survey_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[CsatResponse], int]:
    """List CSAT responses for a ticket with optional filtering by survey."""
    logger.debug(
        "Listing CSAT responses: tenant_id=%s, ticket_id=%s, survey_id=%s, limit=%s, offset=%s",
        tenant_id,
        ticket_id,
        csat_survey_id,
        limit,
        offset,
    )
    query = db.query(CsatResponse).filter(
        CsatResponse.tenant_id == tenant_id,
        CsatResponse.ticket_id == ticket_id,
    )
    if csat_survey_id:
        query = query.filter(CsatResponse.csat_survey_id == csat_survey_id)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(CsatResponse.submitted_at.asc())
    return query.all(), total


def create_csat_response(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    request: TenantCreateCsatResponse | AdminCreateCsatResponse,
    created_by: str,
) -> CsatResponse:
    """Create a new CSAT response and publish a created event."""
    logger.debug(
        "Creating CSAT response: tenant_id=%s, ticket_id=%s, rating=%s",
        tenant_id,
        ticket_id,
        request.rating,
    )
    # Parse submitted_at if provided
    def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
        if ts is None:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid datetime format: {ts}",
            )

    submitted_at = _parse_iso(request.submitted_at) if hasattr(request, "submitted_at") else None
    resp = CsatResponse(
        tenant_id=tenant_id,
        csat_survey_id=request.csat_survey_id,
        ticket_id=ticket_id,
        contact_id=request.contact_id,
        rating=request.rating,
        comment=request.comment,
        submitted_at=submitted_at or datetime.utcnow(),
        created_by=created_by,
    )
    db.add(resp)
    commit_or_raise(db, refresh=resp, action="create CSAT response")
    snapshot = _snapshot(resp)
    CsatResponseProducer.send_csat_response_created(tenant_id=tenant_id, payload=snapshot)
    return resp


def get_csat_response(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    response_id: uuid.UUID,
) -> CsatResponse:
    """Retrieve a CSAT response by ID within a tenant context."""
    resp = (
        db.query(CsatResponse)
        .filter(
            CsatResponse.id == response_id,
            CsatResponse.tenant_id == tenant_id,
        )
        .first()
    )
    if not resp:
        logger.info(
            "CSAT response not found: tenant_id=%s, id=%s", tenant_id, response_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSAT response not found")
    return resp


def update_csat_response(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    response_id: uuid.UUID,
    request: CsatResponseUpdate,
    updated_by: str,
) -> CsatResponse:
    """Update an existing CSAT response and publish an update event.

    Only administrators should invoke this operation.
    """
    resp = get_csat_response(db, tenant_id=tenant_id, response_id=response_id)
    updates: Dict[str, Any] = {}
    def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
        if ts is None:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid datetime format: {ts}",
            )

    if request.csat_survey_id is not None:
        updates["csat_survey_id"] = request.csat_survey_id
    if request.contact_id is not None:
        updates["contact_id"] = request.contact_id
    if request.rating is not None:
        updates["rating"] = request.rating
    if request.comment is not None:
        updates["comment"] = request.comment
    if request.submitted_at is not None:
        updates["submitted_at"] = _parse_iso(request.submitted_at)
    delta = _compute_delta(resp, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(resp, field, value)
        commit_or_raise(db, refresh=resp, action="update CSAT response")
        snapshot = _snapshot(resp)
        CsatResponseProducer.send_csat_response_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return resp


def delete_csat_response(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    response_id: uuid.UUID,
) -> None:
    """Delete a CSAT response and publish a deletion event.

    Only administrators should invoke this operation.
    """
    resp = get_csat_response(db, tenant_id=tenant_id, response_id=response_id)
    db.delete(resp)
    commit_or_raise(db, action="delete CSAT response")
    deleted_dt = datetime.utcnow().isoformat()
    CsatResponseProducer.send_csat_response_deleted(
        tenant_id=tenant_id, deleted_dt=deleted_dt
    )
    return None


__all__ = [
    "list_csat_responses",
    "create_csat_response",
    "get_csat_response",
    "update_csat_response",
    "delete_csat_response",
]