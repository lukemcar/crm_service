"""
Event message schemas for list (segment) lifecycle events.

Lists group records based on filter definitions and are used for
segmentation and marketing.  These events inform other services when
lists are created, updated or deleted.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ListBaseMessage(BaseModel):
    """Base fields common to all list events."""

    tenant_id: UUID


class ListCreatedMessage(ListBaseMessage):
    """Event emitted when a list is created."""

    payload: Dict[str, Any]


class ListUpdatedMessage(ListBaseMessage):
    """Event emitted when a list is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class ListDeletedMessage(ListBaseMessage):
    """Event emitted when a list is deleted."""

    deleted_dt: Optional[str] = None
