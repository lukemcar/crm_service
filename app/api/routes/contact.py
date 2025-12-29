"""FastAPI router for Contact endpoints.

Provides CRUD operations on contacts.  Each endpoint enforces tenant
scoping by requiring a tenant_id parameter in the path or header.  In a
real application, tenant_id and user_id would be extracted from JWT
claims; here they are passed explicitly for simplicity.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.services import contact_service


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[schemas.ContactRead])
def list_contacts(
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    db: Session = Depends(get_db),
) -> List[schemas.ContactRead]:
    contacts = contact_service.list_contacts(db, tenant_id)
    return contacts  # FastAPI will handle conversion to schema


@router.post("/", response_model=schemas.ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    contact_in: schemas.ContactCreate,
    db: Session = Depends(get_db),
) -> schemas.ContactRead:
    contact = contact_service.create_contact(db, tenant_id, user_id, contact_in)
    return contact


@router.get("/{contact_id}", response_model=schemas.ContactRead)
def get_contact(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    contact_id: UUID = Path(..., description="Contact ID"),
    db: Session = Depends(get_db),
) -> schemas.ContactRead:
    contact = contact_service.get_contact(db, contact_id, tenant_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=schemas.ContactRead)
def update_contact(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    user_id: UUID | None = Query(None, description="User performing the operation"),
    contact_id: UUID = Path(..., description="Contact ID"),
    contact_in: schemas.ContactUpdate,
    db: Session = Depends(get_db),
) -> schemas.ContactRead:
    contact = contact_service.get_contact(db, contact_id, tenant_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    updated = contact_service.update_contact(db, contact, user_id, contact_in)
    return updated


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_contact(
    *,
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    contact_id: UUID = Path(..., description="Contact ID"),
    db: Session = Depends(get_db),
) -> Response:
    contact = contact_service.get_contact(db, contact_id, tenant_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact_service.delete_contact(db, contact)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
