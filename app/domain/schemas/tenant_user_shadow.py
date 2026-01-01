"""
Pydantic schemas for tenant user shadow projections.

These models define the shapes of responses returned by the
tenant_user_shadow endpoints.  Since this domain is read‑only within
CRM, only response models are provided.  Instances are created via
SQLAlchemy models and validated using ``from_attributes``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TenantUserShadowOut(BaseModel):
    """Response model representing a projected tenant user."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    display_name: Optional[str] = Field(None, description="Display name of the user")
    email: Optional[str] = Field(None, description="Email address of the user")
    is_active: bool = Field(..., description="Whether the user is active")
    created_at: datetime = Field(..., description="Timestamp when the projection was created")
    updated_at: datetime = Field(..., description="Timestamp when the projection was last updated")

    # Configure the model to allow attribute-based population from ORM objects
    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TenantUserShadowOut",
]
