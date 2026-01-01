"""
Pydantic schemas for SLA Target domain.

These models define request and response structures for creating,
updating and retrieving SLA targets.  Targets define response and
resolution time thresholds for tickets under a specific SLA policy.
Separate create models are provided for tenant and admin contexts.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SlaTargetBase(BaseModel):
    """Shared attributes for SLA target creation and update."""

    sla_policy_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the parent SLA policy"
    )
    priority: Optional[str] = Field(
        default=None,
        description="Ticket priority to which this target applies (low, normal, high, urgent)",
    )
    first_response_minutes: Optional[int] = Field(
        default=None, ge=0, description="Minutes until first response is due"
    )
    next_response_minutes: Optional[int] = Field(
        default=None, ge=0, description="Minutes until next response is due"
    )
    resolution_minutes: Optional[int] = Field(
        default=None, ge=0, description="Minutes until resolution is due"
    )


class TenantCreateSlaTarget(SlaTargetBase):
    """Request model for creating an SLA target in a tenant context."""

    sla_policy_id: uuid.UUID = Field(
        ..., description="Identifier of the parent SLA policy"
    )
    priority: str = Field(
        ..., description="Ticket priority (low, normal, high, urgent)"
    )


class AdminCreateSlaTarget(SlaTargetBase):
    """Request model for creating an SLA target via admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the target"
    )
    sla_policy_id: uuid.UUID = Field(
        ..., description="Identifier of the parent SLA policy"
    )
    priority: str = Field(
        ..., description="Ticket priority (low, normal, high, urgent)"
    )


class SlaTargetUpdate(SlaTargetBase):
    """Request model for updating an existing SLA target."""

    # All fields optional on update; changing sla_policy_id or priority is
    # allowed but will be treated as a replacement of the existing target.
    sla_policy_id: Optional[uuid.UUID] = Field(
        default=None, description="Identifier of the parent SLA policy"
    )
    priority: Optional[str] = Field(
        default=None, description="Ticket priority (low, normal, high, urgent)"
    )
    first_response_minutes: Optional[int] = Field(
        default=None, ge=0, description="Minutes until first response is due"
    )
    next_response_minutes: Optional[int] = Field(
        default=None, ge=0, description="Minutes until next response is due"
    )
    resolution_minutes: Optional[int] = Field(
        default=None, ge=0, description="Minutes until resolution is due"
    )


class SlaTargetOut(BaseModel):
    """Response model representing an SLA target."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    sla_policy_id: uuid.UUID
    priority: str
    first_response_minutes: Optional[int] = None
    next_response_minutes: Optional[int] = None
    resolution_minutes: Optional[int] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "SlaTargetBase",
    "TenantCreateSlaTarget",
    "AdminCreateSlaTarget",
    "SlaTargetUpdate",
    "SlaTargetOut",
]
