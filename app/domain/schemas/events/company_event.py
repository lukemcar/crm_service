"""
Event models for Company lifecycle.

This module defines the payload schemas for company-related events emitted via
the messaging layer.  Each event type corresponds to a CRUD operation on
Company entities.  A delta structure is provided for update events
describing granular changes across base attributes and nested collections.

These models follow the conventions used throughout the existing codebase
and wrap payloads in Pydantic BaseModel classes for easy serialization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyDelta(BaseModel):
    """Represents the set of changes applied to a company.

    The ``base_fields`` dictionary captures updates to top‑level company
    attributes.  Added and updated lists for nested resources contain
    snapshot dictionaries of the new state, whereas deleted lists contain
    only the identifiers of the removed objects.

    CompanyRelationship and ContactCompanyRelationship changes are
    excluded from this delta structure.
    """

    # Base company fields that changed: key -> new value
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


class CompanyCreatedEvent(BaseModel):
    """Payload for a company created event.

    Contains the ``tenant_id`` of the owning tenant and a full snapshot of
    the newly created company.  Downstream consumers can inspect the
    snapshot to initialize caches or perform additional processing.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(..., description="Full company snapshot")


class CompanyUpdatedEvent(BaseModel):
    """Payload for a company updated event.

    ``changes`` contains the delta object describing exactly what
    changed, while ``payload`` is the full snapshot of the company
    after the update.  Consumers may choose to use one or both
    depending on their needs.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: CompanyDelta = Field(..., description="Delta describing modifications")
    payload: Dict[str, Any] = Field(..., description="Full company snapshot after update")


class CompanyDeletedEvent(BaseModel):
    """Payload for a company deleted event.

    Only the ``tenant_id`` and an optional timestamp of deletion are
    included.  Consumers can assume that the company and all nested
    data have been removed from the system.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(None, description="ISO timestamp of when the company was deleted")
