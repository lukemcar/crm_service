"""Event models for CSAT survey lifecycle.

Defines payload schemas for events emitted when CSAT surveys are
created, updated, or deleted. Each event includes the tenant
identifier and relevant payload or delta information.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CsatSurveyDelta(BaseModel):
    """Represents the set of changed base fields for a CSAT survey."""

    base_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Mapping of modified field names to their new values",
    )


class CsatSurveyCreatedEvent(BaseModel):
    """Payload for a csat_survey.created event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    payload: Dict[str, Any] = Field(
        ..., description="Full CSAT survey snapshot after creation"
    )


class CsatSurveyUpdatedEvent(BaseModel):
    """Payload for a csat_survey.updated event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    changes: CsatSurveyDelta = Field(
        ..., description="Delta describing modifications to base fields"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Full CSAT survey snapshot after update"
    )


class CsatSurveyDeletedEvent(BaseModel):
    """Payload for a csat_survey.deleted event."""

    tenant_id: UUID = Field(..., description="Tenant identifier")
    deleted_dt: Optional[str] = Field(
        None,
        description="ISO timestamp of when the CSAT survey was deleted",
    )


__all__ = [
    "CsatSurveyDelta",
    "CsatSurveyCreatedEvent",
    "CsatSurveyUpdatedEvent",
    "CsatSurveyDeletedEvent",
]