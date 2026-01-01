"""Tenant‑scoped endpoints for CSAT surveys.

This router exposes CRUD operations on CSAT surveys for a specific
tenant. Surveys can be listed, created, updated, retrieved, and
deleted. Audit fields are populated from the ``X-User`` header when
provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.csat_survey import (
    TenantCreateCsatSurvey,
    CsatSurveyUpdate,
    CsatSurveyOut,
)
from app.domain.services import csat_survey_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/csat_surveys",
    tags=["CSAT Surveys"],
)


@router.get("", response_model=List[CsatSurveyOut])
def list_csat_surveys_endpoint(
    tenant_id: UUID,
    is_active: Optional[bool] = Query(
        None, description="Filter surveys by active status"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[CsatSurveyOut]:
    """List CSAT surveys for a tenant with optional active filter and pagination."""
    surveys, _ = csat_survey_service.list_csat_surveys(
        db,
        tenant_id=tenant_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return [CsatSurveyOut.model_validate(s, from_attributes=True) for s in surveys]


@router.post("", response_model=CsatSurveyOut, status_code=status.HTTP_201_CREATED)
def create_csat_survey_endpoint(
    tenant_id: UUID,
    survey_in: TenantCreateCsatSurvey,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatSurveyOut:
    """Create a new CSAT survey for a tenant."""
    created_user = x_user or "anonymous"
    survey = csat_survey_service.create_csat_survey(
        db,
        tenant_id=tenant_id,
        request=survey_in,
        created_by=created_user,
    )
    return CsatSurveyOut.model_validate(survey, from_attributes=True)


@router.get("/{survey_id}", response_model=CsatSurveyOut)
def get_csat_survey_endpoint(
    tenant_id: UUID,
    survey_id: UUID,
    db: Session = Depends(get_db),
) -> CsatSurveyOut:
    """Retrieve a CSAT survey by ID within a tenant."""
    survey = csat_survey_service.get_csat_survey(
        db,
        tenant_id=tenant_id,
        survey_id=survey_id,
    )
    return CsatSurveyOut.model_validate(survey, from_attributes=True)


@router.put("/{survey_id}", response_model=CsatSurveyOut)
def update_csat_survey_endpoint(
    tenant_id: UUID,
    survey_id: UUID,
    survey_update: CsatSurveyUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatSurveyOut:
    """Update a CSAT survey for a tenant."""
    updated_user = x_user or "anonymous"
    survey = csat_survey_service.update_csat_survey(
        db,
        tenant_id=tenant_id,
        survey_id=survey_id,
        request=survey_update,
        updated_by=updated_user,
    )
    return CsatSurveyOut.model_validate(survey, from_attributes=True)


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_csat_survey_endpoint(
    tenant_id: UUID,
    survey_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a CSAT survey for a tenant."""
    csat_survey_service.delete_csat_survey(
        db,
        tenant_id=tenant_id,
        survey_id=survey_id,
    )
    return None


__all__ = [
    "list_csat_surveys_endpoint",
    "create_csat_survey_endpoint",
    "get_csat_survey_endpoint",
    "update_csat_survey_endpoint",
    "delete_csat_survey_endpoint",
]