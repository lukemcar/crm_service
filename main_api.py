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
    company_router,
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