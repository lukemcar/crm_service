"""FastAPI router for Company endpoints.

Provides CRUD operations on companies.  Tenancy is enforced via a
tenant_id query parameter.  In a real system, tenant and user
information would come from JWT claims.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import company_service


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[schemas.CompanyRead])
def list_companies(
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.CompanyRead]:
    companies = company_service.list_companies(db, tenant_id)
    return companies


@router.post("/", response_model=schemas.CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    company_in: schemas.CompanyCreate,
    db: Session = Depends(get_db),
) -> schemas.CompanyRead:
    company = company_service.create_company(db, tenant_id, user_id, company_in)
    return company


@router.get("/{company_id}", response_model=schemas.CompanyRead)
def get_company(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    company_id: UUID = Path(..., description="Company ID"),
    db: Session = Depends(get_db),
) -> schemas.CompanyRead:
    company = company_service.get_company(db, company_id, tenant_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=schemas.CompanyRead)
def update_company(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    company_id: UUID = Path(..., description="Company ID"),
    company_in: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
) -> schemas.CompanyRead:
    company = company_service.get_company(db, company_id, tenant_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    updated = company_service.update_company(db, company, user_id, company_in)
    return updated


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_company(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    company_id: UUID = Path(..., description="Company ID"),
    db: Session = Depends(get_db),
) -> Response:
    company = company_service.get_company(db, company_id, tenant_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    company_service.delete_company(db, company)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
