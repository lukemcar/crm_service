"""Aggregate import for API routers.

This module collects all route modules and exposes a list of routers
that can be included in the FastAPI application.  When adding a new
entity, import its router here.
"""

from .pipeline import router as pipeline_router
from .pipeline_stage import router as pipeline_stage_router
from .deal import router as deal_router
from .activity import router as activity_router
from .list import router as list_router
from .list_membership import router as list_membership_router
from .association import router as association_router
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

__all__ = [
    "contact_router",
    "company_router",
    "pipeline_router",
    "pipeline_stage_router",
    "deal_router",
    "activity_router",
    "list_router",
    "list_membership_router",
    "association_router",
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
]