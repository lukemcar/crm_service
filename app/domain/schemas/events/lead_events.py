"""
Pydantic schemas for lead lifecycle events.

These models define the payloads sent through the messaging layer when
leads are created, updated or deleted.  They mirror the shape of the
tenant group event models, including both the change set and the
full snapshot of the lead for updates.  Consumers can rely on these
models to deserialize and process lead events consistently.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LeadCreatedMessage(BaseModel):
    """Event emitted when a lead is created.

    ``tenant_id`` identifies the owning tenant.  ``payload`` contains a
    snapshot of the newly created lead, including its ``lead_id`` and all
    relevant fields.  Additional metadata may be included in the
    payload depending on the consuming service's requirements.
    """

    tenant_id: UUID = Field(..., description="Identifier of the tenant that owns the lead")
    payload: Dict[str, Any] = Field(..., description="Snapshot of the newly created lead")


class LeadUpdatedMessage(BaseModel):
    """Event emitted when a lead is updated via full update or patch.

    ``changes`` contains only the fields that have changed relative to
    the previous state, while ``payload`` holds the full snapshot of
    the lead after the update.  Consumers can use ``changes`` to
    minimize processing or to generate concise audit trails.
    """

    tenant_id: UUID = Field(..., description="Identifier of the tenant that owns the lead")
    changes: Dict[str, Any] = Field(..., description="Subset of lead attributes that changed")
    payload: Dict[str, Any] = Field(..., description="Full snapshot of the updated lead")


class LeadDeletedMessage(BaseModel):
    """Event emitted when a lead is deleted.

    The ``deleted_dt`` is an ISO 8601 timestamp capturing when the
    deletion occurred.  Consumers should treat the absence of
    ``deleted_dt`` as meaning that the producer did not capture the
    timestamp.
    """

    tenant_id: UUID = Field(..., description="Identifier of the tenant that owned the deleted lead")
    deleted_dt: Optional[str] = Field(
        None,
        description=(
            "ISO 8601 timestamp at which the lead was deleted.  May be null if not provided."
        ),
    )
