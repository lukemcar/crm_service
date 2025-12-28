"""
Event message schemas for deal lifecycle events.

Deals represent revenue opportunities moving through a pipeline.  These
events are emitted to notify other services when deals are created,
updated or deleted.  Additional events for stage changes or closing
deals may be added in the future.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class DealBaseMessage(BaseModel):
    """Base fields common to all deal events."""

    tenant_id: UUID


class DealCreatedMessage(DealBaseMessage):
    """Event emitted when a deal is created."""

    payload: Dict[str, Any]


class DealUpdatedMessage(DealBaseMessage):
    """Event emitted when a deal is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class DealDeletedMessage(DealBaseMessage):
    """Event emitted when a deal is deleted."""

    deleted_dt: Optional[str] = None
