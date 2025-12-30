"""
Pydantic models for Contact API endpoints.

This module defines request and response schemas used by the Contact
service and its nested resources.  Models enforce validation for
contact base attributes and nested collections such as phone numbers,
emails, addresses, social profiles, notes and company relationships.

Tenant and Admin create/update variants are provided along with
search and pagination criteria.  Response models include nested
objects to provide a complete view of a contact.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    # Base
    "ContactBase",
    "TenantCreateContact",
    "AdminCreateContact",
    # Search and list
    "ContactSearchCriteria",
    # Nested request/response models
    "ContactPhoneNumberCreateRequest",
    "ContactPhoneNumberUpdateRequest",
    "ContactPhoneNumberResponse",
    "ContactEmailCreateRequest",
    "ContactEmailUpdateRequest",
    "ContactEmailResponse",
    "ContactAddressCreateRequest",
    "ContactAddressUpdateRequest",
    "ContactAddressResponse",
    "ContactSocialProfileCreateRequest",
    "ContactSocialProfileUpdateRequest",
    "ContactSocialProfileResponse",
    "ContactNoteCreateRequest",
    "ContactNoteUpdateRequest",
    "ContactNoteResponse",
    "ContactCompanyRelationshipCreateRequest",
    "ContactCompanyRelationshipUpdateRequest",
    "ContactCompanyRelationshipResponse",
    # Response models
    "ContactOut",
]


# ---------------------------------------------------------------------------
# Nested resource models
# ---------------------------------------------------------------------------


class ContactPhoneNumberCreateRequest(BaseModel):
    """Request model for creating a contact phone number."""

    phone_raw: str = Field(..., max_length=50)
    phone_e164: Optional[str] = Field(default=None, max_length=20)
    phone_type: Optional[str] = Field(default="mobile", max_length=50)
    is_primary: Optional[bool] = Field(default=False)
    is_sms_capable: Optional[bool] = Field(default=False)
    is_verified: Optional[bool] = Field(default=False)


class ContactPhoneNumberUpdateRequest(BaseModel):
    """Request model for updating a contact phone number."""

    phone_raw: Optional[str] = Field(default=None, max_length=50)
    phone_e164: Optional[str] = Field(default=None, max_length=20)
    phone_type: Optional[str] = Field(default=None, max_length=50)
    is_primary: Optional[bool] = None
    is_sms_capable: Optional[bool] = None
    is_verified: Optional[bool] = None


class ContactPhoneNumberResponse(BaseModel):
    """Response model representing a contact phone number."""

    id: uuid.UUID
    phone_raw: str
    phone_e164: Optional[str] = None
    phone_type: str
    is_primary: bool
    is_sms_capable: bool
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ContactEmailCreateRequest(BaseModel):
    """Request model for creating a contact email."""

    email: str = Field(..., max_length=255)
    email_type: Optional[str] = Field(default="work", max_length=50)
    is_primary: Optional[bool] = Field(default=False)
    is_verified: Optional[bool] = Field(default=False)


class ContactEmailUpdateRequest(BaseModel):
    """Request model for updating a contact email."""

    email: Optional[str] = Field(default=None, max_length=255)
    email_type: Optional[str] = Field(default=None, max_length=50)
    is_primary: Optional[bool] = None
    is_verified: Optional[bool] = None


class ContactEmailResponse(BaseModel):
    """Response model representing a contact email."""

    id: uuid.UUID
    email: str
    email_type: str
    is_primary: bool
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ContactAddressCreateRequest(BaseModel):
    """Request model for creating a contact address."""

    address_type: Optional[str] = Field(default="home", max_length=50)
    label: Optional[str] = Field(default=None, max_length=100)
    is_primary: Optional[bool] = Field(default=False)
    line1: str = Field(..., max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    line3: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(..., max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country_code: Optional[str] = Field(default="US", max_length=2)


class ContactAddressUpdateRequest(BaseModel):
    """Request model for updating a contact address."""

    address_type: Optional[str] = Field(default=None, max_length=50)
    label: Optional[str] = Field(default=None, max_length=100)
    is_primary: Optional[bool] = None
    line1: Optional[str] = Field(default=None, max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    line3: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country_code: Optional[str] = Field(default=None, max_length=2)


class ContactAddressResponse(BaseModel):
    """Response model representing a contact address."""

    id: uuid.UUID
    address_type: str
    label: Optional[str]
    is_primary: bool
    line1: str
    line2: Optional[str]
    line3: Optional[str]
    city: str
    region: Optional[str]
    postal_code: Optional[str]
    country_code: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ContactSocialProfileCreateRequest(BaseModel):
    """Request model for creating a contact social profile."""

    profile_type: str = Field(..., max_length=50)
    profile_url: str = Field(..., max_length=255)


class ContactSocialProfileUpdateRequest(BaseModel):
    """Request model for updating a contact social profile."""

    profile_type: Optional[str] = Field(default=None, max_length=50)
    profile_url: Optional[str] = Field(default=None, max_length=255)


class ContactSocialProfileResponse(BaseModel):
    """Response model representing a contact social profile."""

    id: uuid.UUID
    profile_type: str
    profile_url: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ContactNoteCreateRequest(BaseModel):
    """Request model for creating a contact note."""

    note_type: Optional[str] = Field(default="note", max_length=50)
    title: Optional[str] = Field(default=None, max_length=255)
    body: str = Field(...)
    noted_at: Optional[datetime] = None
    source_system: Optional[str] = Field(default=None, max_length=100)
    source_ref: Optional[str] = Field(default=None, max_length=255)


class ContactNoteUpdateRequest(BaseModel):
    """Request model for updating a contact note."""

    note_type: Optional[str] = Field(default=None, max_length=50)
    title: Optional[str] = Field(default=None, max_length=255)
    body: Optional[str] = None
    noted_at: Optional[datetime] = None
    source_system: Optional[str] = Field(default=None, max_length=100)
    source_ref: Optional[str] = Field(default=None, max_length=255)


class ContactNoteResponse(BaseModel):
    """Response model representing a contact note."""

    id: uuid.UUID
    note_type: str
    title: Optional[str] = None
    body: str
    noted_at: datetime
    source_system: Optional[str] = None
    source_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ContactCompanyRelationshipCreateRequest(BaseModel):
    """Request model for creating a contact-company relationship."""

    company_id: uuid.UUID
    relationship_type: str = Field(..., max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)
    job_title: Optional[str] = Field(default=None, max_length=255)
    work_email: Optional[str] = Field(default=None, max_length=255)
    work_phone_raw: Optional[str] = Field(default=None, max_length=50)
    work_phone_e164: Optional[str] = Field(default=None, max_length=20)
    work_phone_ext: Optional[str] = Field(default=None, max_length=20)
    is_primary: Optional[bool] = Field(default=False)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = Field(default=True)


class ContactCompanyRelationshipUpdateRequest(BaseModel):
    """Request model for updating a contact-company relationship."""

    relationship_type: Optional[str] = Field(default=None, max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)
    job_title: Optional[str] = Field(default=None, max_length=255)
    work_email: Optional[str] = Field(default=None, max_length=255)
    work_phone_raw: Optional[str] = Field(default=None, max_length=50)
    work_phone_e164: Optional[str] = Field(default=None, max_length=20)
    work_phone_ext: Optional[str] = Field(default=None, max_length=20)
    is_primary: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class ContactCompanyRelationshipResponse(BaseModel):
    """Response model representing a contact-company relationship."""

    id: uuid.UUID
    company_id: uuid.UUID
    relationship_type: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    work_email: Optional[str] = None
    work_phone_raw: Optional[str] = None
    work_phone_e164: Optional[str] = None
    work_phone_ext: Optional[str] = None
    is_primary: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ---------------------------------------------------------------------------
# Contact base and create models
# ---------------------------------------------------------------------------


class ContactBase(BaseModel):
    """Base fields for a contact."""

    first_name: Optional[str] = Field(default=None, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    job_title: Optional[str] = Field(default=None, max_length=255)


class TenantCreateContact(ContactBase):
    """Model for creating a contact within a tenant.

    Nested collections may be supplied to create associated phone numbers,
    emails, addresses, social profiles and notes.  Company relationships
    should be created via the dedicated relationship endpoints.
    """

    phones: Optional[List[ContactPhoneNumberCreateRequest]] = None
    emails: Optional[List[ContactEmailCreateRequest]] = None
    addresses: Optional[List[ContactAddressCreateRequest]] = None
    social_profiles: Optional[List[ContactSocialProfileCreateRequest]] = None
    notes: Optional[List[ContactNoteCreateRequest]] = None


class AdminCreateContact(TenantCreateContact):
    """Model for creating a contact via the admin API.

    Admins must specify the tenant_id when creating a contact.  All
    other fields mirror TenantCreateContact.
    """

    tenant_id: uuid.UUID


class ContactSearchCriteria(BaseModel):
    """Search filters for listing contacts."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None


class ContactOut(ContactBase):
    """Full response model for a contact including nested collections."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    phones: List[ContactPhoneNumberResponse] = Field(default_factory=list)
    emails: List[ContactEmailResponse] = Field(default_factory=list)
    addresses: List[ContactAddressResponse] = Field(default_factory=list)
    social_profiles: List[ContactSocialProfileResponse] = Field(default_factory=list)
    notes: List[ContactNoteResponse] = Field(default_factory=list)
    company_relationships: List[ContactCompanyRelationshipResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")