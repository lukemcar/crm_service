"""Service layer for CSAT surveys.

This module provides CRUD operations for CSAT survey definitions,
ensuring tenant scoping and emitting events upon successful
mutations. Listing operations support optional filtering by active
status and pagination.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.csat_survey import CsatSurvey
from app.domain.schemas.csat_survey import (
    CsatSurveyUpdate,
    TenantCreateCsatSurvey,
    AdminCreateCsatSurvey,
)
from app.domain.schemas.events.csat_survey_event import CsatSurveyDelta
from app.messaging.producers.csat_survey_producer import (
    CsatSurveyMessageProducer as CsatSurveyProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("csat_survey_service")


def _snapshot(survey: CsatSurvey) -> Dict[str, Any]:
    """Return a dictionary representation of a CsatSurvey suitable for event payloads."""
    return {
        "id": survey.id,
        "tenant_id": survey.tenant_id,
        "name": survey.name,
        "is_active": survey.is_active,
        "config": survey.config,
        "created_at": survey.created_at.isoformat() if survey.created_at else None,
        "updated_at": survey.updated_at.isoformat() if survey.updated_at else None,
        "created_by": survey.created_by,
        "updated_by": survey.updated_by,
    }


def _compute_delta(survey: CsatSurvey, updates: Dict[str, Any]) -> CsatSurveyDelta:
    """Compute a delta object for modified base fields on a CSAT survey."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(survey, field)
        if current != value:
            changed[field] = value
    return CsatSurveyDelta(base_fields=changed or None)


def list_csat_surveys(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[CsatSurvey], int]:
    """List CSAT surveys with optional filtering by tenant and active status."""
    logger.debug(
        "Listing CSAT surveys: tenant_id=%s, is_active=%s, limit=%s, offset=%s",
        tenant_id,
        is_active,
        limit,
        offset,
    )
    query = db.query(CsatSurvey)
    if tenant_id:
        query = query.filter(CsatSurvey.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(CsatSurvey.is_active == is_active)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(CsatSurvey.created_at.desc())
    return query.all(), total


def create_csat_survey(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateCsatSurvey | AdminCreateCsatSurvey,
    created_by: str,
) -> CsatSurvey:
    """Create a new CSAT survey and publish a created event."""
    logger.debug("Creating CSAT survey: tenant_id=%s, name=%s", tenant_id, request.name)
    survey = CsatSurvey(
        tenant_id=tenant_id,
        name=request.name,
        is_active=request.is_active if request.is_active is not None else True,
        config=request.config,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(survey)
    commit_or_raise(db, refresh=survey, action="create CSAT survey")
    snapshot = _snapshot(survey)
    CsatSurveyProducer.send_csat_survey_created(tenant_id=tenant_id, payload=snapshot)
    return survey


def get_csat_survey(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    survey_id: uuid.UUID,
) -> CsatSurvey:
    """Retrieve a CSAT survey by ID within a tenant context."""
    survey = (
        db.query(CsatSurvey)
        .filter(
            CsatSurvey.id == survey_id,
            CsatSurvey.tenant_id == tenant_id,
        )
        .first()
    )
    if not survey:
        logger.info("CSAT survey not found: tenant_id=%s, id=%s", tenant_id, survey_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSAT survey not found")
    return survey


def update_csat_survey(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    survey_id: uuid.UUID,
    request: CsatSurveyUpdate,
    updated_by: str,
) -> CsatSurvey:
    """Update an existing CSAT survey and publish an update event."""
    survey = get_csat_survey(db, tenant_id=tenant_id, survey_id=survey_id)
    updates: Dict[str, Any] = {}
    for field in ["name", "is_active", "config"]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(survey, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(survey, field, value)
        survey.updated_by = updated_by
        survey.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=survey, action="update CSAT survey")
        snapshot = _snapshot(survey)
        CsatSurveyProducer.send_csat_survey_updated(
            tenant_id=tenant_id, changes=delta, payload=snapshot
        )
    return survey


def delete_csat_survey(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    survey_id: uuid.UUID,
) -> None:
    """Delete a CSAT survey and publish a deletion event."""
    survey = get_csat_survey(db, tenant_id=tenant_id, survey_id=survey_id)
    db.delete(survey)
    commit_or_raise(db, action="delete CSAT survey")
    deleted_dt = datetime.utcnow().isoformat()
    CsatSurveyProducer.send_csat_survey_deleted(tenant_id=tenant_id, deleted_dt=deleted_dt)
    return None


__all__ = [
    "list_csat_surveys",
    "create_csat_survey",
    "get_csat_survey",
    "update_csat_survey",
    "delete_csat_survey",
]