"""Entry point for the DYNO CRM FastAPI application.

This module creates the FastAPI app, configures middleware and
includes all API routers.  It follows patterns established in the
developer guide and tenant service for consistency.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import Config

from app.api.routes import (
    pipeline_router,
    pipeline_stage_router,
    deal_router,
    activity_router,
    list_router,
    list_membership_router,
    association_router,
    health_router,
    admin_router,
    
    leads_admin_router,
    leads_tenant_router,
    contacts_admin_router,
    contacts_tenant_router,
    contacts_admin_nested_router,
    contacts_tenant_nested_router,
    companies_admin_router,
    companies_tenant_router,
    companies_admin_nested_router,
    companies_tenant_nested_router,    
    tenant_users_shadow_router,
    tenant_groups_shadow_router,
    inbound_channels_tenant_router,
    inbound_channels_admin_router,
    group_profiles_tenant_router,
    group_profiles_admin_router,
    tickets_tenant_router,
    tickets_admin_router,
    tickets_tenant_nested_router,
    tickets_admin_nested_router,
    ticket_forms_tenant_router,
    ticket_forms_admin_router,
    ticket_field_defs_tenant_router,
    ticket_field_defs_admin_router,
    ticket_form_fields_tenant_router,
    ticket_form_fields_admin_router,
    sla_policies_tenant_router,
    sla_policies_admin_router,
    sla_targets_tenant_router,
    sla_targets_admin_router,
    ticket_sla_state_tenant_router,
    ticket_sla_state_admin_router,
    support_views_tenant_router,
    support_views_admin_router,
    support_macros_tenant_router,
    support_macros_admin_router,
    ticket_task_mirrors_admin_router,
    ticket_ai_work_refs_admin_router,
    csat_surveys_tenant_router,
    csat_surveys_admin_router,
    # Knowledge base routers
    kb_categories_tenant_router,
    kb_categories_admin_router,
    kb_sections_tenant_router,
    kb_sections_admin_router,
    kb_articles_tenant_router,
    kb_articles_admin_router,
    kb_article_revisions_tenant_router,
    kb_article_revisions_admin_router,
    kb_article_feedback_tenant_router,
    kb_article_feedback_admin_router,
)

# Initialise logging and telemetry when the app is created.  Doing
# this at module import time ensures configuration occurs before any
# log statements are emitted or spans are created.  The telemetry
# module gracefully falls back to no-op implementations if
# OpenTelemetry is unavailable.
from app.core.logging import configure_logging, get_logger
from app.core.telemetry import init_tracing, instrument_fastapi

from app.util.liquibase import apply_changelog

configure_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run tasks on startup and shutdown of the FastAPI application."""
    logger.info("startup_event: CRM Service is starting")
    
    if Config.liquibase_enabled():
        try:
            apply_changelog(Config.liquibase_property_file())
        except Exception as exc:
            logger.error(
                "An error occurred while applying Liquibase changelog", exc_info=exc
            )
    else:
        logger.info("Skipping Liquibase schema validation and update")
    yield
    logger.info("shutdown_event: CRM Service is shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure logging and tracing before creating the app.  Logging
    # configuration happens only once; subsequent calls are idempotent.
    init_tracing(service_name="dyno-crm")
    app = FastAPI(lifespan=lifespan, title="DYNO CRM API", version="0.1.0")

    # Include routers
    app.include_router(contacts_admin_router)
    app.include_router(contacts_tenant_router)
    app.include_router(contacts_admin_nested_router)
    app.include_router(contacts_tenant_nested_router)
    app.include_router(leads_admin_router)
    app.include_router(leads_tenant_router)
    app.include_router(companies_admin_router)
    app.include_router(companies_tenant_router)
    app.include_router(companies_admin_nested_router)
    app.include_router(companies_tenant_nested_router)
    app.include_router(pipeline_router)
    app.include_router(pipeline_stage_router)
    app.include_router(deal_router)
    app.include_router(activity_router)
    app.include_router(list_router)
    app.include_router(list_membership_router)
    app.include_router(association_router)
    # Admin and utility routes (health, metrics, tenant projections)
    app.include_router(health_router)
    app.include_router(admin_router)
    # Support domain tenant projections (read‑only)
    app.include_router(tenant_users_shadow_router)
    app.include_router(tenant_groups_shadow_router)
    # Support domain metadata and channels
    app.include_router(inbound_channels_tenant_router)
    app.include_router(inbound_channels_admin_router)
    # Support domain group profiles
    app.include_router(group_profiles_tenant_router)
    app.include_router(group_profiles_admin_router)
    # Support domain tickets
    app.include_router(tickets_tenant_router)
    app.include_router(tickets_admin_router)
    app.include_router(tickets_tenant_nested_router)
    app.include_router(tickets_admin_nested_router)
    # Support domain ticket forms
    app.include_router(ticket_forms_tenant_router)
    app.include_router(ticket_forms_admin_router)
    # Support domain ticket field definitions
    app.include_router(ticket_field_defs_tenant_router)
    app.include_router(ticket_field_defs_admin_router)
    # Support domain ticket form fields
    app.include_router(ticket_form_fields_tenant_router)
    app.include_router(ticket_form_fields_admin_router)
    # Support domain SLA policies and targets
    app.include_router(sla_policies_tenant_router)
    app.include_router(sla_policies_admin_router)
    app.include_router(sla_targets_tenant_router)
    app.include_router(sla_targets_admin_router)
    # Support domain ticket SLA state
    app.include_router(ticket_sla_state_tenant_router)
    app.include_router(ticket_sla_state_admin_router)
    # Support domain views and macros
    app.include_router(support_views_tenant_router)
    app.include_router(support_views_admin_router)
    app.include_router(support_macros_tenant_router)
    app.include_router(support_macros_admin_router)
    # Support domain task mirrors and AI work refs (admin)
    app.include_router(ticket_task_mirrors_admin_router)
    app.include_router(ticket_ai_work_refs_admin_router)
    # Support domain CSAT surveys
    app.include_router(csat_surveys_tenant_router)
    app.include_router(csat_surveys_admin_router)

    # Knowledge base routers
    app.include_router(kb_categories_tenant_router)
    app.include_router(kb_categories_admin_router)
    app.include_router(kb_sections_tenant_router)
    app.include_router(kb_sections_admin_router)
    app.include_router(kb_articles_tenant_router)
    app.include_router(kb_articles_admin_router)
    app.include_router(kb_article_revisions_tenant_router)
    app.include_router(kb_article_revisions_admin_router)
    app.include_router(kb_article_feedback_tenant_router)
    app.include_router(kb_article_feedback_admin_router)

    # Instrument the FastAPI application for tracing.  This will
    # automatically create spans for incoming requests.  If
    # OpenTelemetry is unavailable, this call logs a warning and
    # returns without raising an exception.
    instrument_fastapi(app)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )