"""
Event models for CompanyRelationship lifecycle.

This module defines the payload schemas for events emitted when
relationships between two companies are created, updated or deleted.
These relationships capture roles and optional date ranges between
companies.  Relationship events are emitted separately from company
update events so consumers can process them independently.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyRelationshipCreatedEvent(BaseModel):
    """Payload for a created company relationship event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    from_company_id: UUID = Field(..., description="ID of the company initiating the relationship")
    to_company_id: UUID = Field(..., description="ID of the company receiving the relationship")
    payload: Dict[str, Any] = Field(..., description="Full snapshot of the new relationship")


class CompanyRelationshipUpdatedEvent(BaseModel):
    """Payload for an updated company relationship event.

    ``changes`` contains only those attributes that were modified.
    ``payload`` is the full snapshot after the update.
    """

    tenant_id: UUID = Field(..., description="Tenant identifier")
    from_company_id: UUID = Field(..., description="ID of the company initiating the relationship")
    to_company_id: UUID = Field(..., description="ID of the company receiving the relationship")
    changes: Dict[str, Any] = Field(..., description="Changed attributes")
    payload: Dict[str, Any] = Field(..., description="Full snapshot of the updated relationship")


class CompanyRelationshipDeletedEvent(BaseModel):
    """Payload for a deleted company relationship event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    from_company_id: UUID = Field(..., description="ID of the company initiating the relationship")
    to_company_id: UUID = Field(..., description="ID of the company receiving the relationship")
    deleted_dt: Optional[str] = Field(None, description="ISO timestamp of when the relationship was deleted")
