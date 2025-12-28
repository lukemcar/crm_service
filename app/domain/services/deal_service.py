"""Service layer for Deal operations.

This module encapsulates database interactions and business logic for
creating, retrieving, updating and deleting deals.  All functions
enforce multi‑tenant isolation by scoping queries to the provided
tenant_id.  Where appropriate, callers are expected to validate
foreign key references (e.g. pipeline and stage) prior to calling
these functions.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.deal import Deal
from app.domain.schemas.deal import DealCreate, DealUpdate


def list_deals(db: Session, tenant_id: uuid.UUID) -> Iterable[Deal]:
    """Return all deals for the given tenant."""
    return db.query(Deal).filter(Deal.tenant_id == tenant_id).all()


def get_deal(db: Session, deal_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Deal]:
    """Fetch a single deal by ID within the tenant."""
    return (
        db.query(Deal)
        .filter(Deal.id == deal_id, Deal.tenant_id == tenant_id)
        .first()
    )


def create_deal(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    deal_in: DealCreate,
) -> Deal:
    """Create a new deal for the tenant.

    The caller should ensure that the referenced pipeline and stage
    belong to the same tenant before creating the deal.
    """
    deal = Deal(
        tenant_id=tenant_id,
        name=deal_in.name,
        amount=deal_in.amount,
        expected_close_date=deal_in.expected_close_date,
        pipeline_id=deal_in.pipeline_id,
        stage_id=deal_in.stage_id,
        probability=deal_in.probability,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def update_deal(
    db: Session,
    deal: Deal,
    user_id: Optional[uuid.UUID],
    deal_in: DealUpdate,
) -> Deal:
    """Update fields of an existing deal.

    Only provided fields are updated.  Caller must perform any
    necessary foreign key validation before invoking this function.
    """
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
    deal.updated_by = user_id
    db.commit()
    db.refresh(deal)
    return deal


def delete_deal(db: Session, deal: Deal) -> None:
    """Delete the specified deal."""
    db.delete(deal)
    db.commit()