"""
Tenant‑scoped nested resource endpoints for companies.

This router exposes CRUD operations on a company's phone numbers, emails,
addresses, social profiles, notes and company‑to‑company relationships, as
well as contact relationships (company contacts) from the company
perspective.  All endpoints enforce tenant scoping and emit
appropriate events via the service layer.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.services.company_service import (
    list_company_phones,
    add_company_phone,
    update_company_phone,
    delete_company_phone,
    list_company_emails,
    add_company_email,
    update_company_email,
    delete_company_email,
    list_company_addresses,
    add_company_address,
    update_company_address,
    delete_company_address,
    list_company_social_profiles,
    add_company_social_profile,
    update_company_social_profile,
    delete_company_social_profile,
    list_company_notes,
    add_company_note,
    update_company_note,
    delete_company_note,
    list_company_relationships,
    add_company_relationship,
    update_company_relationship,
    delete_company_relationship,
    list_company_contacts,
    add_company_contact,
    update_company_contact,
    delete_company_contact,
)
from app.domain.schemas.company import (
    CompanyPhoneNumberCreateRequest,
    CompanyPhoneNumberUpdateRequest,
    CompanyPhoneNumberResponse,
    CompanyEmailCreateRequest,
    CompanyEmailUpdateRequest,
    CompanyEmailResponse,
    CompanyAddressCreateRequest,
    CompanyAddressUpdateRequest,
    CompanyAddressResponse,
    CompanySocialProfileCreateRequest,
    CompanySocialProfileUpdateRequest,
    CompanySocialProfileResponse,
    CompanyNoteCreateRequest,
    CompanyNoteUpdateRequest,
    CompanyNoteResponse,
    CompanyRelationshipCreateRequest,
    CompanyRelationshipUpdateRequest,
    CompanyRelationshipResponse,
    CompanyContactRelationshipCreateRequest,
    CompanyContactRelationshipUpdateRequest,
    CompanyContactRelationshipResponse,
)

from app.core.db import get_db


router = APIRouter(
    prefix="/tenants/{tenant_id}/companies/{company_id}",
    tags=["Company Nested Resources"],
)


# ---------------------------------------------------------------------------
# Phone number endpoints
# ---------------------------------------------------------------------------


@router.get("/phone-numbers", response_model=List[CompanyPhoneNumberResponse])
def list_phones(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanyPhoneNumberResponse]:
    phones = list_company_phones(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyPhoneNumberResponse.model_validate(p, from_attributes=True) for p in phones]


@router.post("/phone-numbers", response_model=CompanyPhoneNumberResponse, status_code=status.HTTP_201_CREATED)
def add_phone(
    tenant_id: UUID,
    company_id: UUID,
    phone_in: CompanyPhoneNumberCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyPhoneNumberResponse:
    phone = add_company_phone(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        phone_in=phone_in,
        updated_by=x_user or "anonymous",
    )
    return CompanyPhoneNumberResponse.model_validate(phone, from_attributes=True)


@router.put("/phone-numbers/{phone_id}", response_model=CompanyPhoneNumberResponse)
def update_phone(
    tenant_id: UUID,
    company_id: UUID,
    phone_id: UUID,
    phone_update: CompanyPhoneNumberUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyPhoneNumberResponse:
    phone = update_company_phone(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        phone_id=phone_id,
        phone_update=phone_update,
        updated_by=x_user or "anonymous",
    )
    return CompanyPhoneNumberResponse.model_validate(phone, from_attributes=True)


@router.delete("/phone-numbers/{phone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phone(
    tenant_id: UUID,
    company_id: UUID,
    phone_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_phone(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        phone_id=phone_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Email endpoints
# ---------------------------------------------------------------------------


@router.get("/emails", response_model=List[CompanyEmailResponse])
def list_emails(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanyEmailResponse]:
    emails = list_company_emails(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyEmailResponse.model_validate(e, from_attributes=True) for e in emails]


@router.post("/emails", response_model=CompanyEmailResponse, status_code=status.HTTP_201_CREATED)
def add_email(
    tenant_id: UUID,
    company_id: UUID,
    email_in: CompanyEmailCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyEmailResponse:
    email = add_company_email(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        email_in=email_in,
        updated_by=x_user or "anonymous",
    )
    return CompanyEmailResponse.model_validate(email, from_attributes=True)


@router.put("/emails/{email_id}", response_model=CompanyEmailResponse)
def update_email(
    tenant_id: UUID,
    company_id: UUID,
    email_id: UUID,
    email_update: CompanyEmailUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyEmailResponse:
    email = update_company_email(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        email_id=email_id,
        email_update=email_update,
        updated_by=x_user or "anonymous",
    )
    return CompanyEmailResponse.model_validate(email, from_attributes=True)


@router.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(
    tenant_id: UUID,
    company_id: UUID,
    email_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_email(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        email_id=email_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Address endpoints
# ---------------------------------------------------------------------------


@router.get("/addresses", response_model=List[CompanyAddressResponse])
def list_addresses(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanyAddressResponse]:
    addresses = list_company_addresses(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyAddressResponse.model_validate(a, from_attributes=True) for a in addresses]


@router.post("/addresses", response_model=CompanyAddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(
    tenant_id: UUID,
    company_id: UUID,
    address_in: CompanyAddressCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyAddressResponse:
    address = add_company_address(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        addr_in=address_in,
        updated_by=x_user or "anonymous",
    )
    return CompanyAddressResponse.model_validate(address, from_attributes=True)


@router.put("/addresses/{address_id}", response_model=CompanyAddressResponse)
def update_address(
    tenant_id: UUID,
    company_id: UUID,
    address_id: UUID,
    address_update: CompanyAddressUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyAddressResponse:
    address = update_company_address(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        address_id=address_id,
        addr_update=address_update,
        updated_by=x_user or "anonymous",
    )
    return CompanyAddressResponse.model_validate(address, from_attributes=True)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    tenant_id: UUID,
    company_id: UUID,
    address_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_address(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        address_id=address_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Social profile endpoints
# ---------------------------------------------------------------------------


@router.get("/social-profiles", response_model=List[CompanySocialProfileResponse])
def list_social_profiles(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanySocialProfileResponse]:
    profiles = list_company_social_profiles(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanySocialProfileResponse.model_validate(s, from_attributes=True) for s in profiles]


@router.post("/social-profiles", response_model=CompanySocialProfileResponse, status_code=status.HTTP_201_CREATED)
def add_social_profile(
    tenant_id: UUID,
    company_id: UUID,
    profile_in: CompanySocialProfileCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanySocialProfileResponse:
    profile = add_company_social_profile(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        profile_in=profile_in,
        updated_by=x_user or "anonymous",
    )
    return CompanySocialProfileResponse.model_validate(profile, from_attributes=True)


@router.put("/social-profiles/{social_profile_id}", response_model=CompanySocialProfileResponse)
def update_social_profile(
    tenant_id: UUID,
    company_id: UUID,
    social_profile_id: UUID,
    profile_update: CompanySocialProfileUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanySocialProfileResponse:
    profile = update_company_social_profile(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        social_profile_id=social_profile_id,
        profile_update=profile_update,
        updated_by=x_user or "anonymous",
    )
    return CompanySocialProfileResponse.model_validate(profile, from_attributes=True)


@router.delete("/social-profiles/{social_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_profile(
    tenant_id: UUID,
    company_id: UUID,
    social_profile_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_social_profile(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        social_profile_id=social_profile_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Note endpoints
# ---------------------------------------------------------------------------


@router.get("/notes", response_model=List[CompanyNoteResponse])
def list_notes(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanyNoteResponse]:
    notes = list_company_notes(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyNoteResponse.model_validate(n, from_attributes=True) for n in notes]


@router.post("/notes", response_model=CompanyNoteResponse, status_code=status.HTTP_201_CREATED)
def add_note(
    tenant_id: UUID,
    company_id: UUID,
    note_in: CompanyNoteCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyNoteResponse:
    note = add_company_note(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        note_in=note_in,
        updated_by=x_user or "anonymous",
    )
    return CompanyNoteResponse.model_validate(note, from_attributes=True)


@router.put("/notes/{note_id}", response_model=CompanyNoteResponse)
def update_note(
    tenant_id: UUID,
    company_id: UUID,
    note_id: UUID,
    note_update: CompanyNoteUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyNoteResponse:
    note = update_company_note(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        note_id=note_id,
        note_update=note_update,
        updated_by=x_user or "anonymous",
    )
    return CompanyNoteResponse.model_validate(note, from_attributes=True)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    tenant_id: UUID,
    company_id: UUID,
    note_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_note(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        note_id=note_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Company relationship endpoints
# ---------------------------------------------------------------------------


@router.get("/relationships", response_model=List[CompanyRelationshipResponse])
def list_relationships(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanyRelationshipResponse]:
    rels = list_company_relationships(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyRelationshipResponse.model_validate(r, from_attributes=True) for r in rels]


@router.post("/relationships", response_model=CompanyRelationshipResponse, status_code=status.HTTP_201_CREATED)
def add_relationship(
    tenant_id: UUID,
    company_id: UUID,
    rel_in: CompanyRelationshipCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyRelationshipResponse:
    rel = add_company_relationship(
        db,
        tenant_id=tenant_id,
        from_company_id=company_id,
        rel_in=rel_in,
        updated_by=x_user or "anonymous",
    )
    return CompanyRelationshipResponse.model_validate(rel, from_attributes=True)


@router.put("/relationships/{relationship_id}", response_model=CompanyRelationshipResponse)
def update_relationship(
    tenant_id: UUID,
    company_id: UUID,
    relationship_id: UUID,
    rel_update: CompanyRelationshipUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyRelationshipResponse:
    rel = update_company_relationship(
        db,
        tenant_id=tenant_id,
        from_company_id=company_id,
        relationship_id=relationship_id,
        rel_update=rel_update,
        updated_by=x_user or "anonymous",
    )
    return CompanyRelationshipResponse.model_validate(rel, from_attributes=True)


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relationship(
    tenant_id: UUID,
    company_id: UUID,
    relationship_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_relationship(
        db,
        tenant_id=tenant_id,
        from_company_id=company_id,
        relationship_id=relationship_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Company contact (contact relationship) endpoints
# ---------------------------------------------------------------------------


@router.get("/contacts", response_model=List[CompanyContactRelationshipResponse])
def list_contacts(
    tenant_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
) -> List[CompanyContactRelationshipResponse]:
    rels = list_company_contacts(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyContactRelationshipResponse.model_validate(r, from_attributes=True) for r in rels]


@router.post("/contacts", response_model=CompanyContactRelationshipResponse, status_code=status.HTTP_201_CREATED)
def add_contact(
    tenant_id: UUID,
    company_id: UUID,
    request: CompanyContactRelationshipCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyContactRelationshipResponse:
    rel = add_company_contact(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        request=request,
        updated_by=x_user or "anonymous",
    )
    return CompanyContactRelationshipResponse.model_validate(rel, from_attributes=True)


@router.put("/contacts/{contact_id}", response_model=CompanyContactRelationshipResponse)
def update_contact(
    tenant_id: UUID,
    company_id: UUID,
    contact_id: UUID,
    request: CompanyContactRelationshipUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CompanyContactRelationshipResponse:
    rel = update_company_contact(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        contact_id=contact_id,
        request=request,
        updated_by=x_user or "anonymous",
    )
    return CompanyContactRelationshipResponse.model_validate(rel, from_attributes=True)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    tenant_id: UUID,
    company_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    delete_company_contact(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        contact_id=contact_id,
        updated_by=x_user or "anonymous",
    )
    return None