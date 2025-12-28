"""Service layer for Company operations.

Provides create, read, update and delete functions for companies.
All queries are scoped by tenant to enforce multi‑tenancy.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.company import Company
from app.domain.schemas.company import CompanyCreate, CompanyUpdate


def list_companies(db: Session, tenant_id: uuid.UUID) -> Iterable[Company]:
    """Return all companies for a given tenant."""
    return db.query(Company).filter(Company.tenant_id == tenant_id).all()


def get_company(db: Session, company_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Company]:
    """Fetch a single company by ID within the tenant."""
    return (
        db.query(Company)
        .filter(Company.id == company_id, Company.tenant_id == tenant_id)
        .first()
    )


def create_company(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    company_in: CompanyCreate,
) -> Company:
    """Create a new company for the tenant."""
    company = Company(
        tenant_id=tenant_id,
        company_name=company_in.company_name,
        domain=company_in.domain,
        industry=company_in.industry,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def update_company(
    db: Session,
    company: Company,
    user_id: Optional[uuid.UUID],
    company_in: CompanyUpdate,
) -> Company:
    """Update fields of an existing company."""
    if company_in.company_name is not None:
        company.company_name = company_in.company_name
    if company_in.domain is not None:
        company.domain = company_in.domain
    if company_in.industry is not None:
        company.industry = company_in.industry
    company.updated_by = user_id
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company: Company) -> None:
    """Delete a company."""
    db.delete(company)
    db.commit()