"""
Pydantic schemas for tenant group shadow projections.

These models define the response structures for the ``tenant_group_shadow``
endpoints.  Because tenant group projections are read‑only in CRM,
only response models are supplied.  Requests to mutate these
resources are not supported.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class CreateTenantGroupShadow:
    tenant_id: uuid.UUID = Field(..., description="Tenant identifier")
    group_name: str = Field(..., description="Name of the group")
    group_key: Optional[str] = Field(None, description="Stable key for orchestration integration")
    description: Optional[str] = Field(None, description="Description of the group")
    is_active: bool = Field(..., description="Whether the group is active")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class TenantGroupShadowOut(BaseModel):
    """Response model representing a projected tenant group."""

    id: uuid.UUID = Field(..., description="Group identifier from the tenant service")
    tenant_id: uuid.UUID = Field(..., description="Tenant identifier")
    group_name: str = Field(..., description="Name of the group")
    group_key: Optional[str] = Field(None, description="Stable key for orchestration integration")
    description: Optional[str] = Field(None, description="Description of the group")
    is_active: bool = Field(..., description="Whether the group is active")
    created_at: datetime = Field(..., description="Timestamp when the projection was created")
    updated_at: datetime = Field(..., description="Timestamp when the projection was last updated")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TenantGroupShadowOut",
]
