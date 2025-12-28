"""Aggregate import for API routers.

This module collects all route modules and exposes a list of routers
that can be included in the FastAPI application.  When adding a new
entity, import its router here.
"""

from .contact import router as contact_router
from .company import router as company_router
from .pipeline import router as pipeline_router
from .pipeline_stage import router as pipeline_stage_router
from .deal import router as deal_router
from .activity import router as activity_router
from .list import router as list_router
from .list_membership import router as list_membership_router
from .association import router as association_router
from .health import router as health_router
from .admin import router as admin_router

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
]