"""Aggregate imports for ORM models.

Import all SQLAlchemy model classes so that SQLAlchemy's declarative base can
discover them when creating tables and reflecting metadata.  This module
provides a convenient location to import new models as they are created.
"""

from .lead import Lead
from .contact import Contact
from .contact_address import ContactAddress
from .contact_email import ContactEmail
from .contact_phone import ContactPhone
from .contact_social_profile import ContactSocialProfile
from .contact_note import ContactNote
from .contact_company_relationship import ContactCompanyRelationship
from .company import Company
from .company_address import CompanyAddress
from .company_email import CompanyEmail
from .company_phone import CompanyPhone
from .company_social_profile import CompanySocialProfile
from .company_note import CompanyNote
from .company_relationship import CompanyRelationship
from .pipeline import Pipeline
from .pipeline_stage import PipelineStage
from .deal import Deal
from .activity import Activity
from .list import List
from .list_membership import ListMembership
from .association import Association
from .tenant_user_shadow import TenantUserShadow
from .tenant_group_shadow import TenantGroupShadow
from .group_profile import GroupProfile
from .inbound_channel import InboundChannel
from .ticket import Ticket
from .ticket_participant import TicketParticipant
from .ticket_tag import TicketTag
from .ticket_message import TicketMessage
from .ticket_attachment import TicketAttachment
from .ticket_assignment import TicketAssignment
from .ticket_audit import TicketAudit
from .ticket_field_def import TicketFieldDef
from .ticket_form import TicketForm
from .ticket_form_field import TicketFormField
from .ticket_field_value import TicketFieldValue
from .sla_policy import SlaPolicy
from .sla_target import SlaTarget
from .ticket_sla_state import TicketSlaState
from .support_view import SupportView
from .support_macro import SupportMacro
from .ticket_task_mirror import TicketTaskMirror
from .ticket_ai_work_ref import TicketAiWorkRef
from .ticket_time_entry import TicketTimeEntry
from .csat_survey import CsatSurvey
from .csat_response import CsatResponse
# Reporting primitives
from .ticket_metrics import TicketMetrics
from .ticket_status_duration import TicketStatusDuration
from .kb_category import KbCategory
from .kb_section import KbSection
from .kb_article import KbArticle
from .kb_article_revision import KbArticleRevision
from .kb_article_feedback import KbArticleFeedback

__all__ = [
    "Lead",
    "Contact",
    "ContactAddress",
    "ContactEmail",
    "ContactPhone",
    "ContactSocialProfile",
    "ContactNote",
    "ContactCompanyRelationship",
    "Company",
    "CompanyAddress",
    "CompanyEmail",
    "CompanyPhone",
    "CompanySocialProfile",
    "CompanyNote",
    "CompanyRelationship",
    "Pipeline",
    "PipelineStage",
    "Deal",
    "Activity",
    "List",
    "ListMembership",
    "Association",
    "TenantUserShadow",
    "TenantGroupShadow",
    "GroupProfile",
    "InboundChannel",
    "Ticket",
    "TicketParticipant",
    "TicketTag",
    "TicketMessage",
    "TicketAttachment",
    "TicketAssignment",
    "TicketAudit",
    "TicketFieldDef",
    "TicketForm",
    "TicketFormField",
    "TicketFieldValue",
    "SlaPolicy",
    "SlaTarget",
    "TicketSlaState",
    "SupportView",
    "SupportMacro",
    "TicketTaskMirror",
    "TicketAiWorkRef",
    "TicketTimeEntry",
    "CsatSurvey",
    "CsatResponse",
    "TicketMetrics",
    "TicketStatusDuration",
    "KbCategory",
    "KbSection",
    "KbArticle",
    "KbArticleRevision",
    "KbArticleFeedback",
]