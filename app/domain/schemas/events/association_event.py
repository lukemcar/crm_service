"""
Event message schemas for association lifecycle events.

Associations link records of different types (e.g., contact to company).
These events are emitted when an association is created or deleted.
Associations are typically immutable – update events are not
necessary; instead delete and recreate an association.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class AssociationBaseMessage(BaseModel):
    """Base fields common to all association events."""

    tenant_id: UUID


class AssociationCreatedMessage(AssociationBaseMessage):
    """Event emitted when an association is created."""

    payload: Dict[str, Any]


class AssociationDeletedMessage(AssociationBaseMessage):
    """Event emitted when an association is deleted."""

    deleted_dt: Optional[str] = None
