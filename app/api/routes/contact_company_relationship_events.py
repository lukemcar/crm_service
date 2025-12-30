"""
Event models for contact/company relationship lifecycle.

Contact‑company relationships represent links between contacts and
companies in the CRM.  This module defines event payloads for
create, update and delete operations on these relationships.  Unlike
contact update events, relationship events are not grouped into a
single delta structure and are emitted separately from contact
updates.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ContactCompanyRelationshipCreatedEvent(BaseModel):
    """Payload for a created contact/company relationship event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    contact_id: UUID = Field(..., description="Contact identifier")
    company_id: UUID = Field(..., description="Company identifier")
    payload: Dict[str, Any] = Field(..., description="Full snapshot of the new relationship")


class ContactCompanyRelationshipUpdatedEvent(BaseModel):
    """Payload for an updated contact/company relationship event.

    ``changes`` contains only those attributes that were modified.
    ``payload`` is the full snapshot after the update.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    contact_id: UUID = Field(..., description="Contact identifier")
    company_id: UUID = Field(..., description="Company identifier")
    changes: Dict[str, Any] = Field(..., description="Changed attributes")
    payload: Dict[str, Any] = Field(..., description="Full snapshot of the updated relationship")


class ContactCompanyRelationshipDeletedEvent(BaseModel):
    """Payload for a deleted contact/company relationship event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    contact_id: UUID = Field(..., description="Contact identifier")
    company_id: UUID = Field(..., description="Company identifier")
    deleted_dt: Optional[str] = Field(None, description="ISO timestamp of when the relationship was deleted")
