"""
Event message schemas for activity lifecycle events.

Activities capture notes, calls, tasks and other actions related
to CRM records.  These events notify subscribers when activities
are created, updated or deleted.  Changes to the status or due
date can be included in the ``changes`` field.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ActivityBaseMessage(BaseModel):
    """Base fields common to all activity events."""

    tenant_id: UUID


class ActivityCreatedMessage(ActivityBaseMessage):
    """Event emitted when an activity is created."""

    payload: Dict[str, Any]


class ActivityUpdatedMessage(ActivityBaseMessage):
    """Event emitted when an activity is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class ActivityDeletedMessage(ActivityBaseMessage):
    """Event emitted when an activity is deleted."""

    deleted_dt: Optional[str] = None
