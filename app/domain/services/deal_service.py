"""
Service layer for Deal operations.

This module follows the canonical service pattern established across CRM
domains.  It provides both tenant‑scoped and admin‑scoped operations for
deals and is responsible for enforcing tenant isolation, validating
parent resources (pipelines and stages) where necessary, committing
transactions via :func:`commit_or_raise` and emitting events through
``DealMessageProducer`` after successful commits.

Audit fields (``created_by`` and ``updated_by``) are strings derived
from the ``X-User`` header.  When no user is supplied, ``"anonymous"``
is used.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, List, Tuple, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.deal import Deal
from app.domain.schemas.deal import DealCreate, DealUpdate, DealRead
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.deal_producer import DealMessageProducer


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _deal_snapshot(deal: Deal) -> Dict[str, Any]:
    """
    Create a dictionary snapshot of a deal for event payloads.

    The snapshot is based on the ``DealRead`` schema to ensure that all
    consumer‑visible fields are captured.  Using ``from_attributes=True``
    allows passing ORM instances directly to the Pydantic model.
    """
    read_model = DealRead.model_validate(deal, from_attributes=True)
    return read_model.model_dump()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def service_list_deals(
    db: Session,
    *,
    tenant_id: Optional[UUID] = None,
    pipeline_id: Optional[UUID] = None,
    stage_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[Deal], int]:
    """
    List deals with optional filtering and pagination.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Additional
    filters on ``pipeline_id`` and ``stage_id`` further narrow the results.

    Returns a tuple of ``(deals, total)`` where ``deals`` is the list of
    ``Deal`` ORM instances and ``total`` is the total number of rows
    matching the criteria (ignoring ``limit`` and ``offset``).
    """
    query = db.query(Deal)
    if tenant_id:
        query = query.filter(Deal.tenant_id == tenant_id)
    if pipeline_id:
        query = query.filter(Deal.pipeline_id == pipeline_id)
    if stage_id:
        query = query.filter(Deal.stage_id == stage_id)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_get_deal(
    db: Session,
    *,
    tenant_id: UUID,
    deal_id: UUID,
) -> Deal:
    """
    Retrieve a single deal by ID for a tenant.

    Raises ``HTTPException`` with status 404 if the deal is not found.
    """
    deal = (
        db.query(Deal)
        .filter(Deal.id == deal_id, Deal.tenant_id == tenant_id)
        .first()
    )
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    return deal


def service_create_deal(
    db: Session,
    *,
    tenant_id: UUID,
    deal_in: DealCreate,
    created_user: str,
) -> Deal:
    """
    Create a new deal and emit a ``deal.created`` event.

    The caller must validate that the referenced pipeline and stage belong
    to the specified tenant prior to calling this function.
    """
    deal = Deal(
        tenant_id=tenant_id,
        name=deal_in.name,
        amount=deal_in.amount,
        expected_close_date=deal_in.expected_close_date,
        pipeline_id=deal_in.pipeline_id,
        stage_id=deal_in.stage_id,
        probability=deal_in.probability,
        # Ownership and assignment fields
        owned_by_user_id=getattr(deal_in, "owned_by_user_id", None),
        owned_by_group_id=getattr(deal_in, "owned_by_group_id", None),
        assigned_user_id=getattr(deal_in, "assigned_user_id", None),
        assigned_group_id=getattr(deal_in, "assigned_group_id", None),
        # Deal categorization and forecasting
        deal_type=getattr(deal_in, "deal_type", None),
        forecast_probability=getattr(deal_in, "forecast_probability", None),
        close_date=getattr(deal_in, "close_date", None),
        created_by=created_user,
        updated_by=created_user,
    )
    db.add(deal)
    # Commit the transaction.  If an integrity error occurs, it will be raised
    # from commit_or_raise and the caller should handle it accordingly.
    commit_or_raise(db)
    db.refresh(deal)
    # Emit event after commit
    try:
        payload = _deal_snapshot(deal)
        DealMessageProducer.send_deal_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        # Log the error but do not raise; the database transaction already succeeded.
        pass
    return deal


def service_update_deal(
    db: Session,
    *,
    tenant_id: UUID,
    deal_id: UUID,
    deal_in: DealUpdate,
    modified_user: str,
) -> Deal:
    """
    Update an existing deal and emit a ``deal.updated`` event if changes are detected.

    Only fields explicitly provided in ``deal_in`` are updated.  The caller
    should validate any foreign keys (pipeline_id, stage_id) prior to calling
    this function.
    """
    # Fetch the current deal
    deal = service_get_deal(db, tenant_id=tenant_id, deal_id=deal_id)
    # Create snapshot of current state for change detection
    before = _deal_snapshot(deal)
    # Apply updates
    if deal_in.name is not None:
        deal.name = deal_in.name
    if deal_in.amount is not None:
        deal.amount = deal_in.amount
    if deal_in.expected_close_date is not None:
        deal.expected_close_date = deal_in.expected_close_date
    if deal_in.pipeline_id is not None:
        deal.pipeline_id = deal_in.pipeline_id
    if deal_in.stage_id is not None:
        deal.stage_id = deal_in.stage_id
    if deal_in.probability is not None:
        deal.probability = deal_in.probability
    # Update ownership fields
    if getattr(deal_in, "owned_by_user_id", None) is not None:
        deal.owned_by_user_id = deal_in.owned_by_user_id
    if getattr(deal_in, "owned_by_group_id", None) is not None:
        deal.owned_by_group_id = deal_in.owned_by_group_id
    # Update assignment fields
    if getattr(deal_in, "assigned_user_id", None) is not None:
        deal.assigned_user_id = deal_in.assigned_user_id
    if getattr(deal_in, "assigned_group_id", None) is not None:
        deal.assigned_group_id = deal_in.assigned_group_id
    # Update deal categorization and forecasting
    if getattr(deal_in, "deal_type", None) is not None:
        deal.deal_type = deal_in.deal_type
    if getattr(deal_in, "forecast_probability", None) is not None:
        deal.forecast_probability = deal_in.forecast_probability
    if getattr(deal_in, "close_date", None) is not None:
        deal.close_date = deal_in.close_date
    deal.updated_by = modified_user
    # Commit changes
    commit_or_raise(db)
    db.refresh(deal)
    # Determine changes and emit event if any
    after = _deal_snapshot(deal)
    changes = {
        key: after[key]
        for key in after.keys()
        if before.get(key) != after.get(key)
    }
    if changes:
        try:
            DealMessageProducer.send_deal_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=after,
            )
        except Exception:
            # Swallow messaging exceptions to avoid masking DB success
            pass
    return deal


def service_delete_deal(
    db: Session,
    *,
    tenant_id: UUID,
    deal_id: UUID,
) -> None:
    """
    Delete a deal and emit a ``deal.deleted`` event.

    Raises 404 if the deal is not found.
    """
    deal = service_get_deal(db, tenant_id=tenant_id, deal_id=deal_id)
    db.delete(deal)
    commit_or_raise(db)
    # Emit deletion event
    try:
        deleted_dt = datetime.utcnow().isoformat()
        DealMessageProducer.send_deal_deleted(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
    except Exception:
        pass