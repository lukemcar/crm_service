"""
Pydantic models for Company API endpoints.

This module defines request and response schemas used by the Company
service and its nested resources.  Models enforce validation for
company base attributes and nested collections such as phone numbers,
emails, addresses, social profiles, and notes.  Relationship models
cover both company‑to‑company relationships and contact‑company
relationships (company contacts endpoint).

Tenant and Admin create/update variants are provided along with
search and pagination criteria.  Response models include nested
objects to provide a complete view of a company.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Nested resource models
# ---------------------------------------------------------------------------


class CompanyPhoneNumberCreateRequest(BaseModel):
    """Request model for creating a company phone number."""

    phone_raw: str = Field(..., max_length=50)
    phone_e164: Optional[str] = Field(default=None, max_length=20)
    phone_ext: Optional[str] = Field(default=None, max_length=20)
    phone_type: Optional[str] = Field(default="main", max_length=50)
    is_primary: Optional[bool] = Field(default=False)
    is_sms_capable: Optional[bool] = Field(default=False)
    is_verified: Optional[bool] = Field(default=False)


class CompanyPhoneNumberUpdateRequest(BaseModel):
    """Request model for updating a company phone number."""

    phone_raw: Optional[str] = Field(default=None, max_length=50)
    phone_e164: Optional[str] = Field(default=None, max_length=20)
    phone_ext: Optional[str] = Field(default=None, max_length=20)
    phone_type: Optional[str] = Field(default=None, max_length=50)
    is_primary: Optional[bool] = None
    is_sms_capable: Optional[bool] = None
    is_verified: Optional[bool] = None


class CompanyPhoneNumberResponse(BaseModel):
    """Response model representing a company phone number."""

    id: uuid.UUID
    phone_raw: str
    phone_e164: Optional[str] = None
    phone_ext: Optional[str] = None
    phone_type: str
    is_primary: bool
    is_sms_capable: bool
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CompanyEmailCreateRequest(BaseModel):
    """Request model for creating a company email."""

    email: str = Field(..., max_length=255)
    email_type: Optional[str] = Field(default="work", max_length=50)
    is_primary: Optional[bool] = Field(default=False)
    is_verified: Optional[bool] = Field(default=False)


class CompanyEmailUpdateRequest(BaseModel):
    """Request model for updating a company email."""

    email: Optional[str] = Field(default=None, max_length=255)
    email_type: Optional[str] = Field(default=None, max_length=50)
    is_primary: Optional[bool] = None
    is_verified: Optional[bool] = None


class CompanyEmailResponse(BaseModel):
    """Response model representing a company email."""

    id: uuid.UUID
    email: str
    email_type: str
    is_primary: bool
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CompanyAddressCreateRequest(BaseModel):
    """Request model for creating a company address."""

    address_type: Optional[str] = Field(default="office", max_length=50)
    label: Optional[str] = Field(default=None, max_length=100)
    is_primary: Optional[bool] = Field(default=False)
    line1: str = Field(..., max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    line3: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(..., max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country_code: Optional[str] = Field(default="US", max_length=2)


class CompanyAddressUpdateRequest(BaseModel):
    """Request model for updating a company address."""

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


class CompanyAddressResponse(BaseModel):
    """Response model representing a company address."""

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
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CompanySocialProfileCreateRequest(BaseModel):
    """Request model for creating a company social profile."""

    profile_type: str = Field(..., max_length=50)
    profile_url: str = Field(..., max_length=255)


class CompanySocialProfileUpdateRequest(BaseModel):
    """Request model for updating a company social profile."""

    profile_type: Optional[str] = Field(default=None, max_length=50)
    profile_url: Optional[str] = Field(default=None, max_length=255)


class CompanySocialProfileResponse(BaseModel):
    """Response model representing a company social profile."""

    id: uuid.UUID
    profile_type: str
    profile_url: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CompanyNoteCreateRequest(BaseModel):
    """Request model for creating a company note."""

    note_type: Optional[str] = Field(default="note", max_length=50)
    title: Optional[str] = Field(default=None, max_length=255)
    body: str = Field(...)
    noted_at: Optional[datetime] = None
    source_system: Optional[str] = Field(default=None, max_length=100)
    source_ref: Optional[str] = Field(default=None, max_length=255)


class CompanyNoteUpdateRequest(BaseModel):
    """Request model for updating a company note."""

    note_type: Optional[str] = Field(default=None, max_length=50)
    title: Optional[str] = Field(default=None, max_length=255)
    body: Optional[str] = None
    noted_at: Optional[datetime] = None
    source_system: Optional[str] = Field(default=None, max_length=100)
    source_ref: Optional[str] = Field(default=None, max_length=255)


class CompanyNoteResponse(BaseModel):
    """Response model representing a company note."""

    id: uuid.UUID
    note_type: str
    title: Optional[str] = None
    body: str
    noted_at: datetime
    source_system: Optional[str] = None
    source_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CompanyRelationshipCreateRequest(BaseModel):
    """Request model for creating a company‑to‑company relationship."""

    to_company_id: uuid.UUID
    from_role: str = Field(..., max_length=50)
    to_role: str = Field(..., max_length=50)
    is_active: Optional[bool] = Field(default=True)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class CompanyRelationshipUpdateRequest(BaseModel):
    """Request model for updating a company‑to‑company relationship."""

    from_role: Optional[str] = Field(default=None, max_length=50)
    to_role: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class CompanyRelationshipResponse(BaseModel):
    """Response model representing a company‑to‑company relationship."""

    id: uuid.UUID
    from_company_id: uuid.UUID
    to_company_id: uuid.UUID
    from_role: str
    to_role: str
    is_active: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CompanyContactRelationshipCreateRequest(BaseModel):
    """Request model for creating a contact‑company relationship via the company endpoint."""

    contact_id: uuid.UUID
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


class CompanyContactRelationshipUpdateRequest(BaseModel):
    """Request model for updating a contact‑company relationship via the company endpoint."""

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


class CompanyContactRelationshipResponse(BaseModel):
    """Response model representing a contact‑company relationship from the company perspective."""

    id: uuid.UUID
    contact_id: uuid.UUID
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
# Company base and create models
# ---------------------------------------------------------------------------


class CompanyBase(BaseModel):
    """Base fields for a company."""

    name: Optional[str] = Field(default=None, max_length=255)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=255)


class TenantCreateCompany(CompanyBase):
    """Model for creating a company within a tenant.

    Nested collections may be supplied to create associated phone numbers,
    emails, addresses, social profiles and notes.  Company relationships
    and contact relationships should be created via the dedicated
    relationship endpoints.
    """

    name: str = Field(..., max_length=255)
    phones: Optional[List[CompanyPhoneNumberCreateRequest]] = None
    emails: Optional[List[CompanyEmailCreateRequest]] = None
    addresses: Optional[List[CompanyAddressCreateRequest]] = None
    social_profiles: Optional[List[CompanySocialProfileCreateRequest]] = None
    notes: Optional[List[CompanyNoteCreateRequest]] = None


class AdminCreateCompany(TenantCreateCompany):
    """Model for creating a company via the admin API.

    Admins must specify the tenant_id when creating a company.  All
    other fields mirror TenantCreateCompany.
    """

    tenant_id: uuid.UUID


class CompanySearchCriteria(BaseModel):
    """Search filters for listing companies."""

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None


class CompanyOut(CompanyBase):
    """Full response model for a company including nested collections."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    phones: List[CompanyPhoneNumberResponse] = Field(default_factory=list)
    emails: List[CompanyEmailResponse] = Field(default_factory=list)
    addresses: List[CompanyAddressResponse] = Field(default_factory=list)
    social_profiles: List[CompanySocialProfileResponse] = Field(default_factory=list)
    notes: List[CompanyNoteResponse] = Field(default_factory=list)
    relationships: List[CompanyRelationshipResponse] = Field(default_factory=list)
    contact_relationships: List[CompanyContactRelationshipResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    # Base
    "CompanyBase",
    "TenantCreateCompany",
    "AdminCreateCompany",
    # Search and list
    "CompanySearchCriteria",
    # Nested request/response models
    "CompanyPhoneNumberCreateRequest",
    "CompanyPhoneNumberUpdateRequest",
    "CompanyPhoneNumberResponse",
    "CompanyEmailCreateRequest",
    "CompanyEmailUpdateRequest",
    "CompanyEmailResponse",
    "CompanyAddressCreateRequest",
    "CompanyAddressUpdateRequest",
    "CompanyAddressResponse",
    "CompanySocialProfileCreateRequest",
    "CompanySocialProfileUpdateRequest",
    "CompanySocialProfileResponse",
    "CompanyNoteCreateRequest",
    "CompanyNoteUpdateRequest",
    "CompanyNoteResponse",
    "CompanyRelationshipCreateRequest",
    "CompanyRelationshipUpdateRequest",
    "CompanyRelationshipResponse",
    "CompanyContactRelationshipCreateRequest",
    "CompanyContactRelationshipUpdateRequest",
    "CompanyContactRelationshipResponse",
    # Response models
    "CompanyOut",
]