# Import the canonical ActivityMessageProducer.  The alias is no longer
# required because the class name already reflects its purpose.
from .activity_producer import ActivityMessageProducer
# Import the canonical AssociationMessageProducer.  The alias is no longer
# required because the class name already reflects its purpose.
from .association_producer import AssociationMessageProducer
from .company_producer import CompanyMessageProducer
from .contact_producer import ContactMessageProducer
# Deal domain exports: import the canonical DealMessageProducer and backwards
# compatibility alias DealProducer.  Clients should prefer DealMessageProducer
# for clarity, while DealProducer remains for existing imports.
from .deal_producer import DealMessageProducer, DealProducer
from .lead_producer import LeadMessageProducer
# List domain exports: import the canonical ListMessageProducer and backwards
# compatibility alias ListProducer.  Clients should prefer ListMessageProducer
# for clarity, while ListProducer remains for existing imports.
from .list_producer import ListMessageProducer, ListProducer
from .list_membership_producer import (
    ListMembershipMessageProducer,
    ListMembershipProducer,
)
# Pipeline domain exports: import the canonical PipelineMessageProducer and
# backwards compatibility alias PipelineProducer.  Clients should prefer
# PipelineMessageProducer for clarity.
from .pipeline_producer import PipelineMessageProducer, PipelineProducer
# Pipeline stage domain exports: import the canonical PipelineStageMessageProducer
# and alias PipelineStageProducer for backwards compatibility.
from .pipeline_stage_producer import PipelineStageMessageProducer, PipelineStageProducer
from .group_profile_producer import GroupProfileMessageProducer
from .inbound_channel_producer import InboundChannelMessageProducer
from .ticket_producer import TicketMessageProducer
from .ticket_participant_producer import TicketParticipantMessageProducer
from .ticket_tag_producer import TicketTagMessageProducer
from .ticket_message_producer import TicketMessageMessageProducer
from .ticket_attachment_producer import TicketAttachmentMessageProducer
from .ticket_assignment_producer import TicketAssignmentMessageProducer
from .ticket_audit_producer import TicketAuditMessageProducer
from .ticket_form_producer import TicketFormMessageProducer
from .ticket_field_def_producer import TicketFieldDefMessageProducer
from .ticket_form_field_producer import TicketFormFieldMessageProducer
from .ticket_field_value_producer import TicketFieldValueMessageProducer
from .sla_policy_producer import SlaPolicyMessageProducer
from .sla_target_producer import SlaTargetMessageProducer
from .ticket_sla_state_producer import TicketSlaStateMessageProducer
from .support_view_producer import SupportViewMessageProducer
from .support_macro_producer import SupportMacroMessageProducer
from .ticket_task_mirror_producer import TicketTaskMirrorMessageProducer
from .ticket_ai_work_ref_producer import TicketAiWorkRefMessageProducer
from .ticket_time_entry_producer import TicketTimeEntryMessageProducer
from .csat_survey_producer import CsatSurveyMessageProducer
from .csat_response_producer import CsatResponseMessageProducer
from .kb_category_producer import KbCategoryMessageProducer
from .kb_section_producer import KbSectionMessageProducer
from .kb_article_producer import KbArticleMessageProducer
from .kb_article_revision_producer import KbArticleRevisionMessageProducer
from .kb_article_feedback_producer import KbArticleFeedbackMessageProducer
from .ticket_metrics_producer import TicketMetricsMessageProducer
from .ticket_status_duration_producer import TicketStatusDurationMessageProducer
from .automation_action_producer import AutomationActionMessageProducer
from .automation_action_execution_producer import (
    AutomationActionExecutionMessageProducer,
)
from .stage_history_producer import StageHistoryMessageProducer

__all__ = [
    "ActivityMessageProducer",
    "AssociationMessageProducer",
    "CompanyMessageProducer",
    "ContactMessageProducer",
    "DealMessageProducer",
    "DealProducer",
    "LeadMessageProducer",
    "ListMessageProducer",
    "ListProducer",
    "ListMembershipMessageProducer",
    "ListMembershipProducer",
    "PipelineMessageProducer",
    "PipelineStageMessageProducer",
    "GroupProfileMessageProducer",
    "InboundChannelMessageProducer",
    "TicketMessageProducer",
    "TicketParticipantMessageProducer",
    "TicketTagMessageProducer",
    "TicketMessageMessageProducer",
    "TicketAttachmentMessageProducer",
    "TicketAssignmentMessageProducer",
    "TicketAuditMessageProducer",
    "TicketFormMessageProducer",
    "TicketFieldDefMessageProducer",
    "TicketFormFieldMessageProducer",
    "TicketFieldValueMessageProducer",
    "SlaPolicyMessageProducer",
    "SlaTargetMessageProducer",
    "TicketSlaStateMessageProducer",
    "SupportViewMessageProducer",
    "SupportMacroMessageProducer",
    "TicketTaskMirrorMessageProducer",
    "TicketAiWorkRefMessageProducer",
    "TicketTimeEntryMessageProducer",
    "CsatSurveyMessageProducer",
    "CsatResponseMessageProducer",
    "KbCategoryMessageProducer",
    "KbSectionMessageProducer",
    "KbArticleMessageProducer",
    "KbArticleRevisionMessageProducer",
    "KbArticleFeedbackMessageProducer",
    "TicketMetricsMessageProducer",
    "TicketStatusDurationMessageProducer",
    "AutomationActionMessageProducer",
    "AutomationActionExecutionMessageProducer",
    "StageHistoryMessageProducer",
]