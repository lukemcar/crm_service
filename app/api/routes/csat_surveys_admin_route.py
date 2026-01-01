"""Admin‑scoped endpoints for CSAT surveys.

This router exposes CRUD operations on CSAT surveys across tenants.
Administrators can list surveys across tenants (optionally filtering by
tenant), create new surveys specifying the tenant, update surveys, and
delete surveys. Audit fields are populated from the ``X-User`` header.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.schemas.csat_survey import (
    AdminCreateCsatSurvey,
    CsatSurveyUpdate,
    CsatSurveyOut,
)
from app.domain.services import csat_survey_service


router = APIRouter(
    prefix="/admin/csat_surveys",
    tags=["CSAT Surveys"],
)


@router.get("", response_model=List[CsatSurveyOut])
def list_csat_surveys_admin_endpoint(
    tenant_id: Optional[UUID] = Query(
        None, description="If provided, filters surveys by tenant"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter surveys by active status"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[CsatSurveyOut]:
    """List CSAT surveys across tenants with optional tenant and active filters."""
    surveys, _ = csat_survey_service.list_csat_surveys(
        db,
        tenant_id=tenant_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return [CsatSurveyOut.model_validate(s, from_attributes=True) for s in surveys]


@router.post("", response_model=CsatSurveyOut, status_code=status.HTTP_201_CREATED)
def create_csat_survey_admin_endpoint(
    survey_in: AdminCreateCsatSurvey,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatSurveyOut:
    """Create a CSAT survey via the admin API specifying the tenant."""
    created_user = x_user or "anonymous"
    survey = csat_survey_service.create_csat_survey(
        db,
        tenant_id=survey_in.tenant_id,
        request=survey_in,
        created_by=created_user,
    )
    return CsatSurveyOut.model_validate(survey, from_attributes=True)


@router.get("/{survey_id}", response_model=CsatSurveyOut)
def get_csat_survey_admin_endpoint(
    survey_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the survey to scope the search"
    ),
    db: Session = Depends(get_db),
) -> CsatSurveyOut:
    """Retrieve a CSAT survey via the admin API."""
    survey = csat_survey_service.get_csat_survey(
        db,
        tenant_id=tenant_id,
        survey_id=survey_id,
    )
    return CsatSurveyOut.model_validate(survey, from_attributes=True)


@router.put("/{survey_id}", response_model=CsatSurveyOut)
def update_csat_survey_admin_endpoint(
    survey_id: UUID,
    survey_update: CsatSurveyUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the survey to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatSurveyOut:
    """Update a CSAT survey via the admin API."""
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
def delete_csat_survey_admin_endpoint(
    survey_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the survey to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a CSAT survey via the admin API."""
    csat_survey_service.delete_csat_survey(
        db,
        tenant_id=tenant_id,
        survey_id=survey_id,
    )
    return None


__all__ = [
    "list_csat_surveys_admin_endpoint",
    "create_csat_survey_admin_endpoint",
    "get_csat_survey_admin_endpoint",
    "update_csat_survey_admin_endpoint",
    "delete_csat_survey_admin_endpoint",
]