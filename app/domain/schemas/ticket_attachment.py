"""
Pydantic schemas for TicketAttachment.

These models define the request and response structures for managing
file attachments on tickets.  Attachments reference files stored
externally and contain metadata such as the file name, content type,
size, and storage key.  A ticket attachment may optionally link
to a specific ticket message.  Separate request schemas exist for
tenant and admin contexts; admin creation requires specifying
the tenant_id in the payload.  Response models include audit
fields and mirror the ORM model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketAttachmentBase(BaseModel):
    """Shared attributes for creating a ticket attachment."""

    file_name: str = Field(
        ...,
        max_length=255,
        description="Name of the file (without path)",
    )
    content_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="MIME type of the attachment",
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        description="Size of the file in bytes",
    )
    storage_provider: Optional[str] = Field(
        default=None,
        description="Storage provider used to store the file",
        examples=["s3", "gcs", "azure", "local", "other"],
    )
    storage_key: str = Field(
        ...,
        max_length=500,
        description="Key or path to the file in the storage provider",
    )
    checksum_sha256: Optional[str] = Field(
        default=None,
        max_length=64,
        description="SHA‑256 checksum of the file contents",
    )
    ticket_message_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Identifier of the ticket message this attachment belongs to (optional)",
    )


class TenantCreateTicketAttachment(TicketAttachmentBase):
    """Request model for creating a ticket attachment in a tenant context."""

    pass


class AdminCreateTicketAttachment(TicketAttachmentBase):
    """Request model for creating a ticket attachment via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the ticket attachment"
    )


class TicketAttachmentOut(BaseModel):
    """Response model representing a ticket attachment."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    ticket_message_id: Optional[uuid.UUID] = None
    file_name: str
    content_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    storage_provider: Optional[str] = None
    storage_key: str
    checksum_sha256: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketAttachmentBase",
    "TenantCreateTicketAttachment",
    "AdminCreateTicketAttachment",
    "TicketAttachmentOut",
]