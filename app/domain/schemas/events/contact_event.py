"""
Event message schemas for contact lifecycle events.

These Pydantic models define the structure of messages emitted by
the CRM service when contact records are created, updated or
deleted.  Each message embeds the ``tenant_id`` to allow downstream
consumers to scope processing.  The ``payload`` contains a
JSON‑serialisable snapshot of the contact state and a ``changes``
dictionary is provided for update events.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ContactBaseMessage(BaseModel):
    """Base fields common to all contact events."""

    tenant_id: UUID


class ContactCreatedMessage(ContactBaseMessage):
    """Event emitted when a contact is created."""

    payload: Dict[str, Any]


class ContactUpdatedMessage(ContactBaseMessage):
    """Event emitted when a contact is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class ContactDeletedMessage(ContactBaseMessage):
    """Event emitted when a contact is deleted."""

    deleted_dt: Optional[str] = None
