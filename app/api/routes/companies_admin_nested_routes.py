"""
Admin nested resource routes for companies.

These endpoints allow administrators to manage nested resources for
companies across tenants.  All operations require an explicit
``tenant_id`` query parameter to ensure that the company and its
associated nested objects are resolved within the correct tenant
scope.  The routes mirror those available to tenants but do not
include the tenant path prefix.  Company contacts endpoints are
available only to tenant users and are not exposed here.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
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
)

from app.core.db import get_db


router = APIRouter(prefix="/companies/{company_id}", tags=["Company Nested Resources"])


# ---------------------------------------------------------------------------
# Phone number endpoints
# ---------------------------------------------------------------------------


@router.get("/phone-numbers", response_model=List[CompanyPhoneNumberResponse])
def list_phones_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose phone numbers to list"
    ),
    db: Session = Depends(get_db),
) -> List[CompanyPhoneNumberResponse]:
    phones = list_company_phones(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyPhoneNumberResponse.model_validate(p, from_attributes=True) for p in phones]


@router.post(
    "/phone-numbers",
    response_model=CompanyPhoneNumberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_phone_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to add a phone number to"
    ),
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
def update_phone_admin(
    company_id: UUID,
    phone_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose phone number to update"
    ),
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
def delete_phone_admin(
    company_id: UUID,
    phone_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose phone number to delete"
    ),
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
def list_emails_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose emails to list"
    ),
    db: Session = Depends(get_db),
) -> List[CompanyEmailResponse]:
    emails = list_company_emails(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyEmailResponse.model_validate(e, from_attributes=True) for e in emails]


@router.post(
    "/emails",
    response_model=CompanyEmailResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_email_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to add an email to"
    ),
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
def update_email_admin(
    company_id: UUID,
    email_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose email to update"
    ),
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
def delete_email_admin(
    company_id: UUID,
    email_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose email to delete"
    ),
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
def list_addresses_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose addresses to list"
    ),
    db: Session = Depends(get_db),
) -> List[CompanyAddressResponse]:
    addresses = list_company_addresses(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyAddressResponse.model_validate(a, from_attributes=True) for a in addresses]


@router.post(
    "/addresses",
    response_model=CompanyAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_address_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to add an address to"
    ),
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
def update_address_admin(
    company_id: UUID,
    address_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose address to update"
    ),
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
def delete_address_admin(
    company_id: UUID,
    address_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose address to delete"
    ),
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
def list_social_profiles_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose social profiles to list"
    ),
    db: Session = Depends(get_db),
) -> List[CompanySocialProfileResponse]:
    profiles = list_company_social_profiles(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanySocialProfileResponse.model_validate(s, from_attributes=True) for s in profiles]


@router.post(
    "/social-profiles",
    response_model=CompanySocialProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_social_profile_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to add a social profile to"
    ),
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
def update_social_profile_admin(
    company_id: UUID,
    social_profile_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose social profile to update"
    ),
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
def delete_social_profile_admin(
    company_id: UUID,
    social_profile_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose social profile to delete"
    ),
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
def list_notes_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose notes to list"
    ),
    db: Session = Depends(get_db),
) -> List[CompanyNoteResponse]:
    notes = list_company_notes(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyNoteResponse.model_validate(n, from_attributes=True) for n in notes]


@router.post(
    "/notes",
    response_model=CompanyNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_note_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to add a note to"
    ),
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
def update_note_admin(
    company_id: UUID,
    note_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose note to update"
    ),
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
def delete_note_admin(
    company_id: UUID,
    note_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose note to delete"
    ),
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
def list_relationships_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose relationships to list"
    ),
    db: Session = Depends(get_db),
) -> List[CompanyRelationshipResponse]:
    rels = list_company_relationships(db, tenant_id=tenant_id, company_id=company_id)
    return [CompanyRelationshipResponse.model_validate(r, from_attributes=True) for r in rels]


@router.post(
    "/relationships",
    response_model=CompanyRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_relationship_admin(
    company_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company to add a relationship for"
    ),
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
def update_relationship_admin(
    company_id: UUID,
    relationship_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose relationship to update"
    ),
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
def delete_relationship_admin(
    company_id: UUID,
    relationship_id: UUID,
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the company whose relationship to delete"
    ),
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