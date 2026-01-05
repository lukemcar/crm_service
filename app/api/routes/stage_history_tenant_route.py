"""
Tenant FastAPI route for Stage History.

Provides a read-only endpoint to retrieve the stage history for a given
entity.  Stage history entries are appended by service logic when a
pipeline stage transition occurs.  This route supports pagination and
returns results ordered by ``changed_at`` descending.
"""

from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

import app.domain.services.stage_history_service as history_service
from app.domain.schemas.stage_history import StageHistoryRead
from app.domain.schemas.common import PaginationEnvelope
from app.core.db import get_db


router = APIRouter(
    prefix="/tenants/{tenant_id}/stage-history",
    tags=["Stage History"],
)


@router.get("/{entity_type}/{entity_id}", response_model=PaginationEnvelope[StageHistoryRead])
def list_stage_history(
    *,
    tenant_id: UUID = Path(..., description="Tenant ID"),
    entity_type: str = Path(..., description="Entity type (e.g. deal, lead)"),
    entity_id: UUID = Path(..., description="Entity ID"),
    limit: Optional[int] = Query(None, description="Number of records to return"),
    offset: Optional[int] = Query(None, description="Records to skip before returning results"),
    db: Session = Depends(get_db),
) -> PaginationEnvelope[StageHistoryRead]:
    """List stage history records for the specified entity.

    Entries are ordered by ``changed_at`` descending.  Pagination is
    optional.  The entity type should match the domain (e.g. ``deal`` or
    ``lead``) used when recording the transition.
    """
    entries, total = history_service.list_stage_history_by_entity(
        db,
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    items: List[StageHistoryRead] = [
        StageHistoryRead.model_validate(e, from_attributes=True) for e in entries
    ]
    return PaginationEnvelope[StageHistoryRead](
        items=items, total=total, limit=limit, offset=offset
    )
