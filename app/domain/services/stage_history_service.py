"""
Service layer for StageHistory entities.

This module provides operations to record stage transitions and list
historical stage changes for CRM entities.  Stage history entries are
append-only and always associated with a tenant.  After a stage
transition is recorded, an event is emitted via the message producer.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session

from app.domain.models.stage_history import StageHistory
from app.domain.schemas.stage_history import StageHistoryCreate, StageHistoryRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.stage_history_producer import StageHistoryMessageProducer

logger = logging.getLogger("stage_history_service")


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Convert an ISO timestamp string to a datetime object, if provided."""
    if ts is None:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _snapshot(entry: StageHistory) -> Dict[str, Any]:
    """Return a dictionary representation of a StageHistory for event payloads."""
    read_model = StageHistoryRead.model_validate(entry, from_attributes=True)
    return read_model.model_dump(mode="json")


def record_stage_transition(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    entry_in: StageHistoryCreate,
) -> StageHistory:
    """Record a stage transition for an entity and emit an event.

    Parameters
    ----------
    db : Session
        SQLAlchemy session used for persistence.
    tenant_id : UUID
        Identifier of the tenant context.
    entry_in : StageHistoryCreate
        Data describing the stage transition.

    Returns
    -------
    StageHistory
        The persisted stage history record.
    """
    changed_at_dt = _parse_iso(entry_in.changed_at) or datetime.utcnow()
    entry = StageHistory(
        tenant_id=tenant_id,
        entity_type=entry_in.entity_type,
        entity_id=entry_in.entity_id,
        pipeline_id=entry_in.pipeline_id,
        from_stage_id=entry_in.from_stage_id,
        to_stage_id=entry_in.to_stage_id,
        changed_at=changed_at_dt,
        changed_by_user_id=entry_in.changed_by_user_id,
        source=entry_in.source,
    )
    db.add(entry)
    commit_or_raise(db, refresh=entry, action="create stage history")
    # Emit stage history created event after successful commit
    try:
        payload = _snapshot(entry)
        StageHistoryMessageProducer.send_stage_history_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        logger.exception("Failed to publish stage history event")
    return entry


def list_stage_history_by_entity(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[StageHistory], int]:
    """List stage history records for a given entity.

    Results are ordered by ``changed_at`` descending.  Pagination can be
    applied via ``limit`` and ``offset``.
    """
    query = db.query(StageHistory).filter(
        StageHistory.tenant_id == tenant_id,
        StageHistory.entity_type == entity_type,
        StageHistory.entity_id == entity_id,
    )
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(StageHistory.changed_at.desc())
    return query.all(), total


__all__ = ["record_stage_transition", "list_stage_history_by_entity"]