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
from .tenant_user_shadow import TenantUserShadowOut
from .tenant_group_shadow import TenantGroupShadowOut
from .group_profile import (
    GroupProfileBase,
    TenantCreateGroupProfile,
    AdminCreateGroupProfile,
    GroupProfileUpdate,
    GroupProfileOut,
)
from .inbound_channel import (
    InboundChannelBase,
    TenantCreateInboundChannel,
    AdminCreateInboundChannel,
    InboundChannelUpdate,
    InboundChannelOut,
)
from .ticket import (
    TicketBase,
    TenantCreateTicket,
    AdminCreateTicket,
    TicketUpdate,
    TicketOut,
)
from .ticket_participant import (
    TicketParticipantBase,
    TenantCreateTicketParticipant,
    AdminCreateTicketParticipant,
    TicketParticipantOut,
)
from .ticket_tag import (
    TicketTagBase,
    TenantCreateTicketTag,
    AdminCreateTicketTag,
    TicketTagOut,
)
from .ticket_message import (
    TicketMessageBase,
    TenantCreateTicketMessage,
    AdminCreateTicketMessage,
    TicketMessageOut,
)

# Ticket attachment schemas
from .ticket_attachment import (
    TicketAttachmentBase,
    TenantCreateTicketAttachment,
    AdminCreateTicketAttachment,
    TicketAttachmentOut,
)
from .ticket_assignment import (
    TicketAssignmentBase,
    TenantCreateTicketAssignment,
    AdminCreateTicketAssignment,
    TicketAssignmentOut,
)
from .ticket_audit import TicketAuditOut
from .ticket_form import (
    TicketFormBase,
    TenantCreateTicketForm,
    AdminCreateTicketForm,
    TicketFormUpdate,
    TicketFormOut,
)
from .ticket_field_def import (
    TicketFieldDefBase,
    TenantCreateTicketFieldDef,
    AdminCreateTicketFieldDef,
    TicketFieldDefUpdate,
    TicketFieldDefOut,
)

# Ticket form field schemas
from .ticket_form_field import (
    TicketFormFieldBase,
    TenantCreateTicketFormField,
    AdminCreateTicketFormField,
    TicketFormFieldUpdate,
    TicketFormFieldOut,
)

# Ticket field value schemas
from .ticket_field_value import (
    TicketFieldValueBase,
    TenantCreateTicketFieldValue,
    AdminCreateTicketFieldValue,
    TicketFieldValueUpdate,
    TicketFieldValueOut,
)

# SLA policy schemas
from .sla_policy import (
    SlaPolicyBase,
    TenantCreateSlaPolicy,
    AdminCreateSlaPolicy,
    SlaPolicyUpdate,
    SlaPolicyOut,
)

# SLA target schemas
from .sla_target import (
    SlaTargetBase,
    TenantCreateSlaTarget,
    AdminCreateSlaTarget,
    SlaTargetUpdate,
    SlaTargetOut,
)

# Ticket SLA state schemas
from .ticket_sla_state import (
    TicketSlaStateUpdate,
    TicketSlaStateOut,
)

# Support view schemas
from .support_view import (
    SupportViewBase,
    TenantCreateSupportView,
    AdminCreateSupportView,
    SupportViewUpdate,
    SupportViewOut,
)

# Support macro schemas
from .support_macro import (
    SupportMacroBase,
    TenantCreateSupportMacro,
    AdminCreateSupportMacro,
    SupportMacroUpdate,
    SupportMacroOut,
)
from .ticket_task_mirror import (
    TicketTaskMirrorBase,
    AdminUpsertTicketTaskMirror,
    TicketTaskMirrorOut,
)
from .ticket_ai_work_ref import (
    TicketAiWorkRefBase,
    AdminUpsertTicketAiWorkRef,
    TicketAiWorkRefOut,
)

# Time tracking schemas
from .ticket_time_entry import (
    TicketTimeEntryBase,
    TenantCreateTicketTimeEntry,
    AdminCreateTicketTimeEntry,
    TicketTimeEntryUpdate,
    TicketTimeEntryOut,
)

# CSAT survey schemas
from .csat_survey import (
    CsatSurveyBase,
    TenantCreateCsatSurvey,
    AdminCreateCsatSurvey,
    CsatSurveyUpdate,
    CsatSurveyOut,
)

# CSAT response schemas
from .csat_response import (
    CsatResponseBase,
    TenantCreateCsatResponse,
    AdminCreateCsatResponse,
    CsatResponseUpdate,
    CsatResponseOut,
)

# Reporting primitives schemas
from .ticket_metrics import (
    TicketMetricsBase,
    AdminCreateTicketMetrics,
    TicketMetricsUpdate,
    TicketMetricsOut,
)
from .ticket_status_duration import (
    TicketStatusDurationBase,
    AdminCreateTicketStatusDuration,
    AdminUpdateTicketStatusDuration,
    TicketStatusDurationOut,
)

# Knowledge base schemas
from .kb_category import (
    KbCategoryBase,
    TenantCreateKbCategory,
    AdminCreateKbCategory,
    KbCategoryUpdate,
    KbCategoryOut,
)
from .kb_section import (
    KbSectionBase,
    TenantCreateKbSection,
    AdminCreateKbSection,
    KbSectionUpdate,
    KbSectionOut,
)
from .kb_article import (
    KbArticleBase,
    TenantCreateKbArticle,
    AdminCreateKbArticle,
    KbArticleUpdate,
    KbArticleOut,
)
from .kb_article_revision import (
    KbArticleRevisionBase,
    TenantCreateKbArticleRevision,
    AdminCreateKbArticleRevision,
    KbArticleRevisionOut,
)
from .kb_article_feedback import (
    KbArticleFeedbackBase,
    TenantCreateKbArticleFeedback,
    AdminCreateKbArticleFeedback,
    KbArticleFeedbackOut,
)

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
    # Support domain (tenant projections)
    "TenantUserShadowOut",
    "TenantGroupShadowOut",
    # Support domain schemas
    "GroupProfileBase",
    "TenantCreateGroupProfile",
    "AdminCreateGroupProfile",
    "GroupProfileUpdate",
    "GroupProfileOut",
    "InboundChannelBase",
    "TenantCreateInboundChannel",
    "AdminCreateInboundChannel",
    "InboundChannelUpdate",
    "InboundChannelOut",
    # Ticket schemas
    "TicketBase",
    "TenantCreateTicket",
    "AdminCreateTicket",
    "TicketUpdate",
    "TicketOut",
    # Ticket participant schemas
    "TicketParticipantBase",
    "TenantCreateTicketParticipant",
    "AdminCreateTicketParticipant",
    "TicketParticipantOut",
    # Ticket tag schemas
    "TicketTagBase",
    "TenantCreateTicketTag",
    "AdminCreateTicketTag",
    "TicketTagOut",
    # Ticket message schemas
    "TicketMessageBase",
    "TenantCreateTicketMessage",
    "AdminCreateTicketMessage",
    "TicketMessageOut",
    # Ticket attachment schemas
    "TicketAttachmentBase",
    "TenantCreateTicketAttachment",
    "AdminCreateTicketAttachment",
    "TicketAttachmentOut",
    # Ticket assignment schemas
    "TicketAssignmentBase",
    "TenantCreateTicketAssignment",
    "AdminCreateTicketAssignment",
    "TicketAssignmentOut",
    # Ticket audit schemas
    "TicketAuditOut",

    # Ticket form schemas
    "TicketFormBase",
    "TenantCreateTicketForm",
    "AdminCreateTicketForm",
    "TicketFormUpdate",
    "TicketFormOut",

    # Ticket field definition schemas
    "TicketFieldDefBase",
    "TenantCreateTicketFieldDef",
    "AdminCreateTicketFieldDef",
    "TicketFieldDefUpdate",
    "TicketFieldDefOut",

    # Ticket form field schemas
    "TicketFormFieldBase",
    "TenantCreateTicketFormField",
    "AdminCreateTicketFormField",
    "TicketFormFieldUpdate",
    "TicketFormFieldOut",

    # Ticket field value schemas
    "TicketFieldValueBase",
    "TenantCreateTicketFieldValue",
    "AdminCreateTicketFieldValue",
    "TicketFieldValueUpdate",
    "TicketFieldValueOut",

    # SLA policy schemas
    "SlaPolicyBase",
    "TenantCreateSlaPolicy",
    "AdminCreateSlaPolicy",
    "SlaPolicyUpdate",
    "SlaPolicyOut",

    # SLA target schemas
    "SlaTargetBase",
    "TenantCreateSlaTarget",
    "AdminCreateSlaTarget",
    "SlaTargetUpdate",
    "SlaTargetOut",

    # Ticket SLA state schemas
    "TicketSlaStateUpdate",
    "TicketSlaStateOut",

    # Ticket task mirror schemas
    "TicketTaskMirrorBase",
    "AdminUpsertTicketTaskMirror",
    "TicketTaskMirrorOut",

    # Ticket AI work reference schemas
    "TicketAiWorkRefBase",
    "AdminUpsertTicketAiWorkRef",
    "TicketAiWorkRefOut",
    # Ticket time entry schemas
    "TicketTimeEntryBase",
    "TenantCreateTicketTimeEntry",
    "AdminCreateTicketTimeEntry",
    "TicketTimeEntryUpdate",
    "TicketTimeEntryOut",
    # CSAT survey schemas
    "CsatSurveyBase",
    "TenantCreateCsatSurvey",
    "AdminCreateCsatSurvey",
    "CsatSurveyUpdate",
    "CsatSurveyOut",
    # CSAT response schemas
    "CsatResponseBase",
    "TenantCreateCsatResponse",
    "AdminCreateCsatResponse",
    "CsatResponseUpdate",
    "CsatResponseOut",

    # Knowledge base schemas
    "KbCategoryBase",
    "TenantCreateKbCategory",
    "AdminCreateKbCategory",
    "KbCategoryUpdate",
    "KbCategoryOut",
    "KbSectionBase",
    "TenantCreateKbSection",
    "AdminCreateKbSection",
    "KbSectionUpdate",
    "KbSectionOut",
    "KbArticleBase",
    "TenantCreateKbArticle",
    "AdminCreateKbArticle",
    "KbArticleUpdate",
    "KbArticleOut",
    "KbArticleRevisionBase",
    "TenantCreateKbArticleRevision",
    "AdminCreateKbArticleRevision",
    "KbArticleRevisionOut",
    "KbArticleFeedbackBase",
    "TenantCreateKbArticleFeedback",
    "AdminCreateKbArticleFeedback",
    "KbArticleFeedbackOut",
    # Reporting primitives schemas
    "TicketMetricsBase",
    "AdminCreateTicketMetrics",
    "TicketMetricsUpdate",
    "TicketMetricsOut",
    "TicketStatusDurationBase",
    "AdminCreateTicketStatusDuration",
    "AdminUpdateTicketStatusDuration",
    "TicketStatusDurationOut",
]