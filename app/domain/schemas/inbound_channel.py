"""
Pydantic schemas for the InboundChannel domain.

These models define the request and response structures for creating,
updating and retrieving inbound channels.  Separate models exist
for tenant‑scoped and admin‑scoped creation to ensure the correct
tenant context is always provided.  Response models include audit
fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class InboundChannelBase(BaseModel):
    """Shared attributes for inbound channel creation and update."""

    channel_type: str = Field(
        ..., max_length=50, description="Type of channel (email, web, chat, sms, voice, api, internal, social)"
    )
    name: str = Field(..., max_length=255, description="Friendly name for the inbound channel")
    external_ref: Optional[str] = Field(
        default=None, max_length=255, description="Provider identifier (mailbox ID, phone number ID, etc.)"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Non‑secret provider configuration encoded as JSON"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the channel is active and accepting messages"
    )


class TenantCreateInboundChannel(InboundChannelBase):
    """Request model for creating an inbound channel in a tenant context."""
    pass


class AdminCreateInboundChannel(InboundChannelBase):
    """Request model for creating an inbound channel via the admin API."""

    tenant_id: uuid.UUID = Field(..., description="Tenant identifier for the inbound channel")


class InboundChannelUpdate(BaseModel):
    """Request model for updating an existing inbound channel."""

    channel_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Type of channel (email, web, chat, sms, voice, api, internal, social)",
    )
    name: Optional[str] = Field(default=None, max_length=255, description="Friendly name for the inbound channel")
    external_ref: Optional[str] = Field(
        default=None, max_length=255, description="Provider identifier (mailbox ID, phone number ID, etc.)"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Non‑secret provider configuration encoded as JSON"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether the channel is active and accepting messages"
    )


class InboundChannelOut(BaseModel):
    """Response model representing an inbound channel."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    channel_type: str
    name: str
    external_ref: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: Optional[str] = None  # ISO timestamp string
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "InboundChannelBase",
    "TenantCreateInboundChannel",
    "AdminCreateInboundChannel",
    "InboundChannelUpdate",
    "InboundChannelOut",
]