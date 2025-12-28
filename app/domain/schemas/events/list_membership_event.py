"""
Event message schemas for list membership lifecycle events.

List memberships associate records (e.g., contacts) with lists.  When
a membership is created or deleted, these events notify other
systems.  Updates to list membership are rare; thus only created and
deleted events are defined.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ListMembershipBaseMessage(BaseModel):
    """Base fields common to all list membership events."""

    tenant_id: UUID


class ListMembershipCreatedMessage(ListMembershipBaseMessage):
    """Event emitted when a list membership is created."""

    payload: Dict[str, Any]


class ListMembershipDeletedMessage(ListMembershipBaseMessage):
    """Event emitted when a list membership is deleted."""

    deleted_dt: Optional[str] = None
