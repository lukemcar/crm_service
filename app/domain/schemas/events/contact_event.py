"""
Event models for Contact lifecycle.

This module defines the payload schemas for contact-related events
emitted via the messaging layer.  Each event type corresponds to a
CRUD operation on a Contact entity.  The delta structure used by
``ContactUpdatedEvent`` captures granular changes to both base
attributes and nested collections, enabling downstream consumers to
react appropriately to fine‑grained updates.

The event models mirror the conventions used throughout the existing
codebase.  They wrap payloads in simple Pydantic BaseModel classes
which can be serialized to JSON.  See ``contact_producer.py`` for
publishing logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ContactDelta(BaseModel):
    """Represents the set of changes applied to a contact.

    This model captures both top‑level field changes (``base_fields``)
    and modifications to nested collections.  Lists of added and
    updated items contain snapshot dictionaries of the new state,
    while lists of deleted items contain only the identifiers of the
    removed objects.  All attributes are optional; absent attributes
    imply no change for that aspect.
    """

    # Base contact fields that changed: key -> new value
    base_fields: Optional[Dict[str, Any]] = None

    # Changes to phone numbers
    phones_added: Optional[List[Dict[str, Any]]] = None
    phones_updated: Optional[List[Dict[str, Any]]] = None
    phones_deleted: Optional[List[UUID]] = None

    # Changes to emails
    emails_added: Optional[List[Dict[str, Any]]] = None
    emails_updated: Optional[List[Dict[str, Any]]] = None
    emails_deleted: Optional[List[UUID]] = None

    # Changes to addresses
    addresses_added: Optional[List[Dict[str, Any]]] = None
    addresses_updated: Optional[List[Dict[str, Any]]] = None
    addresses_deleted: Optional[List[UUID]] = None

    # Changes to social profiles
    social_profiles_added: Optional[List[Dict[str, Any]]] = None
    social_profiles_updated: Optional[List[Dict[str, Any]]] = None
    social_profiles_deleted: Optional[List[UUID]] = None

    # Changes to notes
    notes_added: Optional[List[Dict[str, Any]]] = None
    notes_updated: Optional[List[Dict[str, Any]]] = None
    notes_deleted: Optional[List[UUID]] = None


class ContactCreatedEvent(BaseModel):
    """Payload for a contact created event.

    Contains the ``tenant_id`` of the owning tenant and a full
    snapshot of the newly created contact.  Downstream consumers can
    inspect the snapshot to initialize caches or perform additional
    processing.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(..., description="Full contact snapshot")


class ContactUpdatedEvent(BaseModel):
    """Payload for a contact updated event.

    ``changes`` contains the delta object describing exactly what
    changed, while ``payload`` is the full snapshot of the contact
    after the update.  Consumers may choose to use one or both
    depending on their needs.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: ContactDelta = Field(..., description="Delta describing modifications")
    payload: Dict[str, Any] = Field(..., description="Full contact snapshot after update")


class ContactDeletedEvent(BaseModel):
    """Payload for a contact deleted event.

    Only the ``tenant_id`` and an optional timestamp of deletion are
    included.  Consumers can assume that the contact and all nested
    data have been removed from the system.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(None, description="ISO timestamp of when the contact was deleted")
