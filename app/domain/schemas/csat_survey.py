"""Pydantic schemas for the CSAT survey domain.

These models describe the structures used to create, update, and
retrieve customer satisfaction surveys. Surveys are defined per
tenant and may include arbitrary configuration data describing the
questions or rating scales.
"""

from __future__ import annotations

import uuid
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field


class CsatSurveyBase(BaseModel):
    """Shared attributes for creating or updating a CSAT survey."""

    name: str = Field(
        ..., max_length=255, description="Name of the survey"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the survey is active and can be used"
    )
    config: Optional[Any] = Field(
        default=None,
        description="Optional JSON configuration for survey questions and rating scales",
    )


class TenantCreateCsatSurvey(CsatSurveyBase):
    """Request model for creating a CSAT survey in a tenant context."""
    pass


class AdminCreateCsatSurvey(CsatSurveyBase):
    """Request model for creating a CSAT survey via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for which the survey will be created"
    )


class CsatSurveyUpdate(BaseModel):
    """Request model for updating a CSAT survey."""

    name: Optional[str] = Field(
        default=None, max_length=255, description="Updated survey name"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the survey should be active or inactive",
    )
    config: Optional[Any] = Field(
        default=None,
        description="Updated survey configuration",
    )


class CsatSurveyOut(BaseModel):
    """Response model representing a CSAT survey."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    is_active: bool
    config: Optional[Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "CsatSurveyBase",
    "TenantCreateCsatSurvey",
    "AdminCreateCsatSurvey",
    "CsatSurveyUpdate",
    "CsatSurveyOut",
]