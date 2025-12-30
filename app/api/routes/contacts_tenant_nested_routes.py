"""
Tenant‑scoped nested resource endpoints for contacts.

This router exposes CRUD operations on phone numbers, emails,
addresses, social profiles, notes and company relationships within a
contact.  All endpoints enforce tenant scoping and emit appropriate
events via the service layer.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.services.contact_service import (
    list_contact_phones,
    add_contact_phone,
    update_contact_phone,
    delete_contact_phone,
    list_contact_emails,
    add_contact_email,
    update_contact_email,
    delete_contact_email,
    list_contact_addresses,
    add_contact_address,
    update_contact_address,
    delete_contact_address,
    list_contact_social_profiles,
    add_contact_social_profile,
    update_contact_social_profile,
    delete_contact_social_profile,
    list_contact_notes,
    add_contact_note,
    update_contact_note,
    delete_contact_note,
    list_contact_company_relationships,
    add_contact_company_relationship,
    update_contact_company_relationship,
    delete_contact_company_relationship,
)

from app.domain.schemas.contact import (
    ContactPhoneNumberCreateRequest,
    ContactPhoneNumberUpdateRequest,
    ContactPhoneNumberResponse,
    ContactEmailCreateRequest,
    ContactEmailUpdateRequest,
    ContactEmailResponse,
    ContactAddressCreateRequest,
    ContactAddressUpdateRequest,
    ContactAddressResponse,
    ContactSocialProfileCreateRequest,
    ContactSocialProfileUpdateRequest,
    ContactSocialProfileResponse,
    ContactNoteCreateRequest,
    ContactNoteUpdateRequest,
    ContactNoteResponse,
    ContactCompanyRelationshipCreateRequest,
    ContactCompanyRelationshipUpdateRequest,
    ContactCompanyRelationshipResponse,
)

from app.core.db import get_db


router = APIRouter(prefix="/tenants/{tenant_id}/contacts/{contact_id}", tags=["Contact Nested Resources"])


# ---------------------------------------------------------------------------
# Phone number endpoints
# ---------------------------------------------------------------------------


@router.get("/phone-numbers", response_model=List[ContactPhoneNumberResponse])
def list_phones(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    phones = list_contact_phones(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactPhoneNumberResponse.model_validate(p, from_attributes=True) for p in phones]


@router.post("/phone-numbers", response_model=ContactPhoneNumberResponse, status_code=status.HTTP_201_CREATED)
def add_phone(
    tenant_id: UUID,
    contact_id: UUID,
    phone_in: ContactPhoneNumberCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    phone = add_contact_phone(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        phone_in=phone_in,
        updated_by=x_user or "anonymous",
    )
    return ContactPhoneNumberResponse.model_validate(phone, from_attributes=True)


@router.put("/phone-numbers/{phone_id}", response_model=ContactPhoneNumberResponse)
def update_phone(
    tenant_id: UUID,
    contact_id: UUID,
    phone_id: UUID,
    phone_update: ContactPhoneNumberUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    phone = update_contact_phone(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        phone_id=phone_id,
        phone_update=phone_update,
        updated_by=x_user or "anonymous",
    )
    return ContactPhoneNumberResponse.model_validate(phone, from_attributes=True)


@router.delete("/phone-numbers/{phone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phone(
    tenant_id: UUID,
    contact_id: UUID,
    phone_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    delete_contact_phone(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        phone_id=phone_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Email endpoints
# ---------------------------------------------------------------------------


@router.get("/emails", response_model=List[ContactEmailResponse])
def list_emails(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    emails = list_contact_emails(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactEmailResponse.model_validate(e, from_attributes=True) for e in emails]


@router.post("/emails", response_model=ContactEmailResponse, status_code=status.HTTP_201_CREATED)
def add_email(
    tenant_id: UUID,
    contact_id: UUID,
    email_in: ContactEmailCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    email = add_contact_email(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        email_in=email_in,
        updated_by=x_user or "anonymous",
    )
    return ContactEmailResponse.model_validate(email, from_attributes=True)


@router.put("/emails/{email_id}", response_model=ContactEmailResponse)
def update_email(
    tenant_id: UUID,
    contact_id: UUID,
    email_id: UUID,
    email_update: ContactEmailUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    email = update_contact_email(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        email_id=email_id,
        email_update=email_update,
        updated_by=x_user or "anonymous",
    )
    return ContactEmailResponse.model_validate(email, from_attributes=True)


@router.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(
    tenant_id: UUID,
    contact_id: UUID,
    email_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    delete_contact_email(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        email_id=email_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Address endpoints
# ---------------------------------------------------------------------------


@router.get("/addresses", response_model=List[ContactAddressResponse])
def list_addresses(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    addresses = list_contact_addresses(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactAddressResponse.model_validate(a, from_attributes=True) for a in addresses]


@router.post("/addresses", response_model=ContactAddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(
    tenant_id: UUID,
    contact_id: UUID,
    address_in: ContactAddressCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    address = add_contact_address(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        addr_in=address_in,
        updated_by=x_user or "anonymous",
    )
    return ContactAddressResponse.model_validate(address, from_attributes=True)


@router.put("/addresses/{address_id}", response_model=ContactAddressResponse)
def update_address(
    tenant_id: UUID,
    contact_id: UUID,
    address_id: UUID,
    address_update: ContactAddressUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    address = update_contact_address(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        address_id=address_id,
        addr_update=address_update,
        updated_by=x_user or "anonymous",
    )
    return ContactAddressResponse.model_validate(address, from_attributes=True)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    tenant_id: UUID,
    contact_id: UUID,
    address_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    delete_contact_address(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        address_id=address_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Social profile endpoints
# ---------------------------------------------------------------------------


@router.get("/social-profiles", response_model=List[ContactSocialProfileResponse])
def list_social_profiles(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    profiles = list_contact_social_profiles(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactSocialProfileResponse.model_validate(p, from_attributes=True) for p in profiles]


@router.post("/social-profiles", response_model=ContactSocialProfileResponse, status_code=status.HTTP_201_CREATED)
def add_social_profile(
    tenant_id: UUID,
    contact_id: UUID,
    sp_in: ContactSocialProfileCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    profile = add_contact_social_profile(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        sp_in=sp_in,
        updated_by=x_user or "anonymous",
    )
    return ContactSocialProfileResponse.model_validate(profile, from_attributes=True)


@router.put("/social-profiles/{social_profile_id}", response_model=ContactSocialProfileResponse)
def update_social_profile(
    tenant_id: UUID,
    contact_id: UUID,
    social_profile_id: UUID,
    sp_update: ContactSocialProfileUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    profile = update_contact_social_profile(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        social_profile_id=social_profile_id,
        sp_update=sp_update,
        updated_by=x_user or "anonymous",
    )
    return ContactSocialProfileResponse.model_validate(profile, from_attributes=True)


@router.delete("/social-profiles/{social_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_profile(
    tenant_id: UUID,
    contact_id: UUID,
    social_profile_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    delete_contact_social_profile(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        social_profile_id=social_profile_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Notes endpoints
# ---------------------------------------------------------------------------


@router.get("/notes", response_model=List[ContactNoteResponse])
def list_notes(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    notes = list_contact_notes(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactNoteResponse.model_validate(n, from_attributes=True) for n in notes]


@router.post("/notes", response_model=ContactNoteResponse, status_code=status.HTTP_201_CREATED)
def add_note(
    tenant_id: UUID,
    contact_id: UUID,
    note_in: ContactNoteCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    note = add_contact_note(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        note_in=note_in,
        updated_by=x_user or "anonymous",
    )
    return ContactNoteResponse.model_validate(note, from_attributes=True)


@router.put("/notes/{note_id}", response_model=ContactNoteResponse)
def update_note(
    tenant_id: UUID,
    contact_id: UUID,
    note_id: UUID,
    note_update: ContactNoteUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    note = update_contact_note(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        note_id=note_id,
        note_update=note_update,
        updated_by=x_user or "anonymous",
    )
    return ContactNoteResponse.model_validate(note, from_attributes=True)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    tenant_id: UUID,
    contact_id: UUID,
    note_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    delete_contact_note(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        note_id=note_id,
        updated_by=x_user or "anonymous",
    )
    return None


# ---------------------------------------------------------------------------
# Company relationship endpoints
# ---------------------------------------------------------------------------


@router.get("/companies", response_model=List[ContactCompanyRelationshipResponse])
def list_company_relationships(
    tenant_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    rels = list_contact_company_relationships(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactCompanyRelationshipResponse.model_validate(r, from_attributes=True) for r in rels]


@router.post("/companies", response_model=ContactCompanyRelationshipResponse, status_code=status.HTTP_201_CREATED)
def add_company_relationship(
    tenant_id: UUID,
    contact_id: UUID,
    rel_in: ContactCompanyRelationshipCreateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    rel = add_contact_company_relationship(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        rel_in=rel_in,
        updated_by=x_user or "anonymous",
    )
    return ContactCompanyRelationshipResponse.model_validate(rel, from_attributes=True)


@router.put("/companies/{company_id}", response_model=ContactCompanyRelationshipResponse)
def update_company_relationship(
    tenant_id: UUID,
    contact_id: UUID,
    company_id: UUID,
    rel_update: ContactCompanyRelationshipUpdateRequest,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    rel = update_contact_company_relationship(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        company_id=company_id,
        rel_update=rel_update,
        updated_by=x_user or "anonymous",
    )
    return ContactCompanyRelationshipResponse.model_validate(rel, from_attributes=True)


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_relationship(
    tenant_id: UUID,
    contact_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
):
    delete_contact_company_relationship(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        company_id=company_id,
        updated_by=x_user or "anonymous",
    )
    return None
