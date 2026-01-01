"""Pydantic schemas for the CSAT response domain.

These models define the request and response structures for creating,
updating (admin only), and retrieving customer satisfaction survey
responses tied to tickets. Responses capture a rating from 1 to 5 and
an optional comment. Separate models exist for tenant and admin
contexts.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CsatResponseBase(BaseModel):
    """Shared attributes when creating or updating a CSAT response."""

    csat_survey_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Identifier of the survey this response pertains to (optional)"
    )
    contact_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Contact identifier of the respondent (optional)"
    )
    rating: int = Field(
        ..., ge=1, le=5, description="Rating between 1 and 5 inclusive"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional free-form comment provided by the respondent",
    )
    submitted_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the response was submitted (ISO 8601 format)",
    )


class TenantCreateCsatResponse(CsatResponseBase):
    """Request model for creating a CSAT response in a tenant context.

    The ticket ID is provided as a path parameter on nested routes and
    therefore omitted here. ``tenant_id`` is also provided via the path.
    """

    pass


class AdminCreateCsatResponse(CsatResponseBase):
    """Request model for creating a CSAT response via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the response will be created"
    )
    ticket_id: uuid.UUID = Field(
        ..., description="Ticket identifier for which the response will be created"
    )


class CsatResponseUpdate(BaseModel):
    """Request model for updating a CSAT response (admin-only).

    Ratings, contact references, and comments may be corrected by
    administrators. ``submitted_at`` may also be updated to correct
    response timestamps.
    """

    csat_survey_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Updated survey identifier"
    )
    contact_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Updated contact identifier"
    )
    rating: Optional[int] = Field(
        default=None,
        ge=1, le=5,
        description="Updated rating between 1 and 5"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Updated comment"
    )
    submitted_at: Optional[str] = Field(
        default=None,
        description="Updated submission timestamp (ISO 8601 format)"
    )


class CsatResponseOut(BaseModel):
    """Response model representing a CSAT response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    csat_survey_id: Optional[uuid.UUID]
    ticket_id: uuid.UUID
    contact_id: Optional[uuid.UUID]
    rating: int
    comment: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "CsatResponseBase",
    "TenantCreateCsatResponse",
    "AdminCreateCsatResponse",
    "CsatResponseUpdate",
    "CsatResponseOut",
]