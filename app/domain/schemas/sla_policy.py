"""
Pydantic schemas for SLA Policy domain.

These models define request and response structures for creating,
updating and retrieving SLA policies.  Separate create models are
provided for tenant and admin contexts.  Response models include all
fields exposed by the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class SlaPolicyBase(BaseModel):
    """Shared attributes for SLA policy creation and update."""

    name: Optional[str] = Field(
        default=None, max_length=255, description="Name of the SLA policy"
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="Description of the policy"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the policy is active"
    )
    match_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON rules to match tickets to this policy"
    )


class TenantCreateSlaPolicy(SlaPolicyBase):
    """Request model for creating an SLA policy in a tenant context."""

    name: str = Field(..., max_length=255, description="Name of the SLA policy")


class AdminCreateSlaPolicy(SlaPolicyBase):
    """Request model for creating an SLA policy via admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the policy")
    name: str = Field(..., max_length=255, description="Name of the SLA policy")


class SlaPolicyUpdate(SlaPolicyBase):
    """Request model for updating an existing SLA policy."""

    # All fields are optional on update
    name: Optional[str] = Field(
        default=None, max_length=255, description="Name of the SLA policy"
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="Description of the policy"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether the policy is active"
    )
    match_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON rules to match tickets to this policy"
    )


class SlaPolicyOut(BaseModel):
    """Response model representing an SLA policy."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    match_rules: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "SlaPolicyBase",
    "TenantCreateSlaPolicy",
    "AdminCreateSlaPolicy",
    "SlaPolicyUpdate",
    "SlaPolicyOut",
]
