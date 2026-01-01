"""
Pydantic schemas for the GroupProfile domain.

These models define request and response structures for creating,
updating and retrieving group profiles.  There are separate
create/update models for tenant and admin contexts to enforce
explicit tenant scoping on admin operations.  Response models
include all fields exposed by the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class GroupProfileBase(BaseModel):
    """Shared attributes for group profile creation and update."""

    profile_type: Optional[str] = Field(
        default="support_queue", max_length=50, description="Type of group profile"
    )
    is_support_queue: Optional[bool] = Field(
        default=True, description="Whether this group functions as a support queue"
    )
    is_assignable: Optional[bool] = Field(
        default=True, description="Whether tickets can be assigned to this group"
    )
    default_sla_policy_id: Optional[uuid.UUID] = Field(
        default=None, description="Default SLA policy ID to apply to tickets"
    )
    routing_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Non-secret JSON config for routing"
    )
    ai_work_mode_default: Optional[str] = Field(
        default="human_only", max_length=50, description="Default AI work mode"
    )
    business_hours_id: Optional[uuid.UUID] = Field(
        default=None, description="Business hours calendar reference"
    )


class TenantCreateGroupProfile(GroupProfileBase):
    """Request model for creating a group profile in a tenant context."""

    group_id: uuid.UUID = Field(..., description="Identifier of the mirrored group")


class AdminCreateGroupProfile(GroupProfileBase):
    """Request model for creating a group profile via admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the profile")
    group_id: uuid.UUID = Field(..., description="Identifier of the mirrored group")


class GroupProfileUpdate(GroupProfileBase):
    """Request model for updating an existing group profile."""

    # All fields are optional on update; group_id cannot be changed
    profile_type: Optional[str] = Field(
        default=None, max_length=50, description="Type of group profile"
    )
    is_support_queue: Optional[bool] = Field(
        default=None, description="Whether this group functions as a support queue"
    )
    is_assignable: Optional[bool] = Field(
        default=None, description="Whether tickets can be assigned to this group"
    )
    default_sla_policy_id: Optional[uuid.UUID] = Field(
        default=None, description="Default SLA policy ID to apply to tickets"
    )
    routing_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Non-secret JSON config for routing"
    )
    ai_work_mode_default: Optional[str] = Field(
        default=None, max_length=50, description="Default AI work mode"
    )
    business_hours_id: Optional[uuid.UUID] = Field(
        default=None, description="Business hours calendar reference"
    )


class GroupProfileOut(BaseModel):
    """Response model representing a group profile."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    group_id: uuid.UUID
    profile_type: str
    is_support_queue: bool
    is_assignable: bool
    default_sla_policy_id: Optional[uuid.UUID] = None
    routing_config: Optional[Dict[str, Any]] = None
    ai_work_mode_default: str
    business_hours_id: Optional[uuid.UUID] = None
    created_at: Optional[str] = None  # using ISO format for datetime
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "GroupProfileBase",
    "TenantCreateGroupProfile",
    "AdminCreateGroupProfile",
    "GroupProfileUpdate",
    "GroupProfileOut",
]
