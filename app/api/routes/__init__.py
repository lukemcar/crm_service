"""Aggregate import for API routers.

This module collects all route modules and exposes a list of routers
that can be included in the FastAPI application.  When adding a new
entity, import its router here.
"""

# Pipeline routes have been split into admin and tenant modules.  Import
# the new routers instead of the legacy pipeline router.
from .pipelines_admin_route import router as pipelines_admin_router
from .pipelines_tenant_route import router as pipelines_tenant_router
from .pipeline_stages_admin_route import router as pipeline_stages_admin_router
from .pipeline_stages_tenant_route import router as pipeline_stages_tenant_router
# Deal routes have been split into admin and tenant modules following the
# canonical pattern.  Import the new routers instead of the legacy deal router.
from .deals_admin_route import router as deals_admin_router
from .deals_tenant_route import router as deals_tenant_router
from .activities_admin_route import router as activities_admin_router
from .activities_tenant_route import router as activities_tenant_router
# List domain: import new admin and tenant routers.  The legacy list router
# is no longer included in the API application.
from .lists_admin_route import router as lists_admin_router
from .lists_tenant_route import router as lists_tenant_router
# List membership routes have been split into admin and tenant modules. Import
# the new routers instead of the legacy list_membership router.
from .list_memberships_admin_route import router as list_memberships_admin_router
from .list_memberships_tenant_route import router as list_memberships_tenant_router
from .associations_admin_route import router as associations_admin_router
from .associations_tenant_route import router as associations_tenant_router
from .health import router as health_router
from .admin import router as admin_router
from .leads_admin_route import router as leads_admin_router
from .leads_tenant_route import router as leads_tenant_router
from .contacts_admin_route import router as contacts_admin_router
from .contacts_tenant_route import router as contacts_tenant_router
from .contacts_admin_nested_routes import router as contacts_admin_nested_router
from .contacts_tenant_nested_routes import router as contacts_tenant_nested_router
from .companies_admin_route import router as companies_admin_router
from .companies_tenant_route import router as companies_tenant_router
from .companies_admin_nested_routes import router as companies_admin_nested_router
from .companies_tenant_nested_routes import router as companies_tenant_nested_router

# Support domain (tenant projections)
from .tenant_users_shadow_tenant_route import router as tenant_users_shadow_router
from .tenant_groups_shadow_tenant_route import router as tenant_groups_shadow_router

# Support domain (metadata and channels)
from .inbound_channels_tenant_route import router as inbound_channels_tenant_router
from .inbound_channels_admin_route import router as inbound_channels_admin_router
from .group_profiles_tenant_route import router as group_profiles_tenant_router
from .group_profiles_admin_route import router as group_profiles_admin_router

from .tickets_tenant_route import router as tickets_tenant_router
from .tickets_admin_route import router as tickets_admin_router
from .tickets_tenant_nested_routes import router as tickets_tenant_nested_router
from .tickets_admin_nested_routes import router as tickets_admin_nested_router
from .ticket_forms_tenant_route import router as ticket_forms_tenant_router
from .ticket_forms_admin_route import router as ticket_forms_admin_router
from .ticket_field_defs_tenant_route import router as ticket_field_defs_tenant_router
from .ticket_field_defs_admin_route import router as ticket_field_defs_admin_router
from .ticket_form_fields_tenant_route import router as ticket_form_fields_tenant_router
from .ticket_form_fields_admin_route import router as ticket_form_fields_admin_router

# SLA policy and target routes
from .sla_policies_tenant_route import router as sla_policies_tenant_router
from .sla_policies_admin_route import router as sla_policies_admin_router
from .sla_targets_tenant_route import router as sla_targets_tenant_router
from .sla_targets_admin_route import router as sla_targets_admin_router

# Ticket SLA state routes
from .ticket_sla_state_tenant_route import router as ticket_sla_state_tenant_router
from .ticket_sla_state_admin_route import router as ticket_sla_state_admin_router

# Support views and macros routes
from .support_views_tenant_route import router as support_views_tenant_router
from .support_views_admin_route import router as support_views_admin_router
from .support_macros_tenant_route import router as support_macros_tenant_router
from .support_macros_admin_route import router as support_macros_admin_router
from .ticket_task_mirrors_admin_route import router as ticket_task_mirrors_admin_router
from .ticket_ai_work_refs_admin_route import router as ticket_ai_work_refs_admin_router
from .csat_surveys_tenant_route import router as csat_surveys_tenant_router
from .csat_surveys_admin_route import router as csat_surveys_admin_router

# Knowledge base routes
from .kb_categories_tenant_route import router as kb_categories_tenant_router
from .kb_categories_admin_route import router as kb_categories_admin_router
from .kb_sections_tenant_route import router as kb_sections_tenant_router
from .kb_sections_admin_route import router as kb_sections_admin_router
from .kb_articles_tenant_route import router as kb_articles_tenant_router
from .kb_articles_admin_route import router as kb_articles_admin_router
from .kb_article_revisions_tenant_route import (
    router as kb_article_revisions_tenant_router,
)
from .kb_article_revisions_admin_route import (
    router as kb_article_revisions_admin_router,
)
from .kb_article_feedback_tenant_route import (
    router as kb_article_feedback_tenant_router,
)
from .kb_article_feedback_admin_route import (
    router as kb_article_feedback_admin_router,
)
# Record watcher routers
from .record_watchers_admin_route import router as record_watchers_admin_router
from .record_watchers_tenant_route import router as record_watchers_tenant_router

# Automation action routers
from .automation_actions_admin_route import router as automation_actions_admin_router
from .automation_actions_tenant_route import router as automation_actions_tenant_router
from .stage_history_tenant_route import router as stage_history_tenant_router

__all__ = [
    "contact_router",
    "company_router",
    "pipelines_admin_router",
    "pipelines_tenant_router",
    "pipeline_stages_admin_router",
    "pipeline_stages_tenant_router",
    "deals_admin_router",
    "deals_tenant_router",
    "activities_admin_router",
    "activities_tenant_router",
    "lists_admin_router",
    "lists_tenant_router",
    "list_memberships_admin_router",
    "list_memberships_tenant_router",
    "associations_admin_router",
    "associations_tenant_router",
    "health_router",
    "admin_router",
    "leads_admin_router",
    "leads_tenant_router",
    "contacts_admin_router",
    "contacts_tenant_router",
    "contacts_admin_nested_router",
    "contacts_tenant_nested_router",
    "companies_admin_router",
    "companies_tenant_router",
    "companies_admin_nested_router",
    "companies_tenant_nested_router",
    # Support domain routers
    "tenant_users_shadow_router",
    "tenant_groups_shadow_router",
    # Support domain routers
    "inbound_channels_tenant_router",
    "inbound_channels_admin_router",
    "group_profiles_tenant_router",
    "group_profiles_admin_router",
    "tickets_tenant_router",
    "tickets_admin_router",
    "tickets_tenant_nested_router",
    "tickets_admin_nested_router",
    "ticket_forms_tenant_router",
    "ticket_forms_admin_router",
    "ticket_field_defs_tenant_router",
    "ticket_field_defs_admin_router",
    "ticket_form_fields_tenant_router",
    "ticket_form_fields_admin_router",
    # SLA policy and target routers
    "sla_policies_tenant_router",
    "sla_policies_admin_router",
    "sla_targets_tenant_router",
    "sla_targets_admin_router",
    # Ticket SLA state routers
    "ticket_sla_state_tenant_router",
    "ticket_sla_state_admin_router",
    # Support views and macros routers
    "support_views_tenant_router",
    "support_views_admin_router",
    "support_macros_tenant_router",
    "support_macros_admin_router",
    "ticket_task_mirrors_admin_router",
    "ticket_ai_work_refs_admin_router",
    # CSAT survey routers
    "csat_surveys_tenant_router",
    "csat_surveys_admin_router",
    # Knowledge base routers
    "kb_categories_tenant_router",
    "kb_categories_admin_router",
    "kb_sections_tenant_router",
    "kb_sections_admin_router",
    "kb_articles_tenant_router",
    "kb_articles_admin_router",
    "kb_article_revisions_tenant_router",
    "kb_article_revisions_admin_router",
    "kb_article_feedback_tenant_router",
    "kb_article_feedback_admin_router",
    # Record watchers
    "record_watchers_admin_router",
    "record_watchers_tenant_router",
    # Automation actions
    "automation_actions_admin_router",
    "automation_actions_tenant_router",
    "stage_history_tenant_router",
]