"""Aggregate imports for Pydantic schemas.

Import all schema classes so that other modules can reference them
without needing to know individual module names.  Add new models to
this file as they are created.
"""

from .contact import (
    # Base
    ContactBase,
    TenantCreateContact,
    AdminCreateContact,
    # Search and list
    ContactSearchCriteria,
    # Nested request/response models
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
    # Response models
    ContactOut,
)
from .company import (
    # Base
    CompanyBase,
    TenantCreateCompany,
    AdminCreateCompany,
    # Search and list
    CompanySearchCriteria,
    # Nested request/response models
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
    # Response models
    CompanyOut,
)
from .lead import (
    LeadData,
    LeadAddressValue,
    LeadNoteValue,
    LeadBase,
    CreateLead,
    UpdateLead,
    LeadOut,
)
from .pipeline import PipelineCreate, PipelineUpdate, PipelineRead
from .pipeline_stage import (
    PipelineStageCreate,
    PipelineStageUpdate,
    PipelineStageRead,
)
from .deal import DealCreate, DealUpdate, DealRead
from .activity import ActivityCreate, ActivityUpdate, ActivityRead
from .list import ListCreate, ListUpdate, ListRead
from .list_membership import ListMembershipCreate, ListMembershipRead
from .association import AssociationCreate, AssociationRead

__all__ = [
    # Lead schemas
    "LeadData",
    "LeadAddressValue",
    "LeadNoteValue",
    "LeadBase",
    "CreateLead",
    "UpdateLead",
    "LeadOut",
    # Contact schemas
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
    # Company schemas
    
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
    # Pipeline schemas
    "PipelineCreate",
    "PipelineUpdate",
    "PipelineRead",
    "PipelineStageCreate",
    "PipelineStageUpdate",
    "PipelineStageRead",
    # Deal schemas
    "DealCreate",
    "DealUpdate",
    "DealRead",
    # Activity schemas
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityRead",
    # List schemas
    "ListCreate",
    "ListUpdate",
    "ListRead",
    "ListMembershipCreate",
    "ListMembershipRead",
    "AssociationCreate",
    "AssociationRead",
]