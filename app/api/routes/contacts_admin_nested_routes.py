"""
Admin nested resource routes for contacts.

These endpoints allow administrators to manage nested resources for
contacts across tenants.  All operations require an explicit
``tenant_id`` query parameter to ensure that the contact and its
associated nested objects are resolved within the correct tenant
scope.  The routes mirror those available to tenants but do not
include the tenant path prefix.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
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


router = APIRouter(prefix="/contacts/{contact_id}", tags=["Contact Nested Resources"])


# ---------------------------------------------------------------------------
# Phone number endpoints
# ---------------------------------------------------------------------------


@router.get("/phone-numbers", response_model=List[ContactPhoneNumberResponse])
def list_phones_admin(
    contact_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the contact whose phone numbers to list"
    ),
    db: Session = Depends(get_db),
) -> List[ContactPhoneNumberResponse]:
    phones = list_contact_phones(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactPhoneNumberResponse.model_validate(p, from_attributes=True) for p in phones]


@router.post(
    "/phone-numbers",
    response_model=ContactPhoneNumberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_phone_admin(
    contact_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to add a phone number to"),
    phone_in: ContactPhoneNumberCreateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactPhoneNumberResponse:
    phone = add_contact_phone(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        phone_in=phone_in,
        updated_by=x_user or "anonymous",
    )
    return ContactPhoneNumberResponse.model_validate(phone, from_attributes=True)


@router.put("/phone-numbers/{phone_id}", response_model=ContactPhoneNumberResponse)
def update_phone_admin(
    contact_id: UUID,
    phone_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose phone number to update"),
    phone_update: ContactPhoneNumberUpdateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactPhoneNumberResponse:
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
def delete_phone_admin(
    contact_id: UUID,
    phone_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose phone number to delete"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
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
def list_emails_admin(
    contact_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the contact whose emails to list"
    ),
    db: Session = Depends(get_db),
) -> List[ContactEmailResponse]:
    emails = list_contact_emails(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactEmailResponse.model_validate(e, from_attributes=True) for e in emails]


@router.post(
    "/emails",
    response_model=ContactEmailResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_email_admin(
    contact_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to add an email to"),
    email_in: ContactEmailCreateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactEmailResponse:
    email = add_contact_email(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        email_in=email_in,
        updated_by=x_user or "anonymous",
    )
    return ContactEmailResponse.model_validate(email, from_attributes=True)


@router.put("/emails/{email_id}", response_model=ContactEmailResponse)
def update_email_admin(
    contact_id: UUID,
    email_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose email to update"),
    email_update: ContactEmailUpdateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactEmailResponse:
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
def delete_email_admin(
    contact_id: UUID,
    email_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose email to delete"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
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
def list_addresses_admin(
    contact_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose addresses to list"),
    db: Session = Depends(get_db),
) -> List[ContactAddressResponse]:
    addresses = list_contact_addresses(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactAddressResponse.model_validate(a, from_attributes=True) for a in addresses]


@router.post(
    "/addresses",
    response_model=ContactAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_address_admin(
    contact_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to add an address to"),
    address_in: ContactAddressCreateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactAddressResponse:
    address = add_contact_address(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        addr_in=address_in,
        updated_by=x_user or "anonymous",
    )
    return ContactAddressResponse.model_validate(address, from_attributes=True)


@router.put("/addresses/{address_id}", response_model=ContactAddressResponse)
def update_address_admin(
    contact_id: UUID,
    address_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose address to update"),
    address_update: ContactAddressUpdateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactAddressResponse:
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
def delete_address_admin(
    contact_id: UUID,
    address_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose address to delete"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
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
def list_social_profiles_admin(
    contact_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose social profiles to list"),
    db: Session = Depends(get_db),
) -> List[ContactSocialProfileResponse]:
    profiles = list_contact_social_profiles(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactSocialProfileResponse.model_validate(p, from_attributes=True) for p in profiles]


@router.post(
    "/social-profiles",
    response_model=ContactSocialProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_social_profile_admin(
    contact_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to add a social profile to"),
    sp_in: ContactSocialProfileCreateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactSocialProfileResponse:
    sp = add_contact_social_profile(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        sp_in=sp_in,
        updated_by=x_user or "anonymous",
    )
    return ContactSocialProfileResponse.model_validate(sp, from_attributes=True)


@router.put("/social-profiles/{social_profile_id}", response_model=ContactSocialProfileResponse)
def update_social_profile_admin(
    contact_id: UUID,
    social_profile_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose social profile to update"),
    sp_update: ContactSocialProfileUpdateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactSocialProfileResponse:
    sp = update_contact_social_profile(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        social_profile_id=social_profile_id,
        sp_update=sp_update,
        updated_by=x_user or "anonymous",
    )
    return ContactSocialProfileResponse.model_validate(sp, from_attributes=True)


@router.delete("/social-profiles/{social_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_profile_admin(
    contact_id: UUID,
    social_profile_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose social profile to delete"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
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
def list_notes_admin(
    contact_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose notes to list"),
    db: Session = Depends(get_db),
) -> List[ContactNoteResponse]:
    notes = list_contact_notes(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactNoteResponse.model_validate(n, from_attributes=True) for n in notes]


@router.post(
    "/notes",
    response_model=ContactNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_note_admin(
    contact_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to add a note to"),
    note_in: ContactNoteCreateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactNoteResponse:
    note = add_contact_note(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        note_in=note_in,
        updated_by=x_user or "anonymous",
    )
    return ContactNoteResponse.model_validate(note, from_attributes=True)


@router.put("/notes/{note_id}", response_model=ContactNoteResponse)
def update_note_admin(
    contact_id: UUID,
    note_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose note to update"),
    note_update: ContactNoteUpdateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactNoteResponse:
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
def delete_note_admin(
    contact_id: UUID,
    note_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose note to delete"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
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
def list_company_relationships_admin(
    contact_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose company relationships to list"),
    db: Session = Depends(get_db),
) -> List[ContactCompanyRelationshipResponse]:
    rels = list_contact_company_relationships(db, tenant_id=tenant_id, contact_id=contact_id)
    return [ContactCompanyRelationshipResponse.model_validate(r, from_attributes=True) for r in rels]


@router.post(
    "/companies",
    response_model=ContactCompanyRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_company_relationship_admin(
    contact_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact to add a company relationship to"),
    rel_in: ContactCompanyRelationshipCreateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactCompanyRelationshipResponse:
    rel = add_contact_company_relationship(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        rel_in=rel_in,
        updated_by=x_user or "anonymous",
    )
    return ContactCompanyRelationshipResponse.model_validate(rel, from_attributes=True)


@router.put("/companies/{company_id}", response_model=ContactCompanyRelationshipResponse)
def update_company_relationship_admin(
    contact_id: UUID,
    company_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose company relationship to update"),
    rel_update: ContactCompanyRelationshipUpdateRequest,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> ContactCompanyRelationshipResponse:
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
def delete_company_relationship_admin(
    contact_id: UUID,
    company_id: UUID,
    *,
    tenant_id: UUID = Query(..., description="Tenant ID of the contact whose company relationship to delete"),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    delete_contact_company_relationship(
        db,
        tenant_id=tenant_id,
        contact_id=contact_id,
        company_id=company_id,
        updated_by=x_user or "anonymous",
    )
    return None
