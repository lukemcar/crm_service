"""Aggregate imports for Pydantic schemas.

Import all schema classes so that other modules can reference them
without needing to know individual module names.  Add new models to
this file as they are created.
"""

from .contact import ContactCreate, ContactUpdate, ContactRead
from .company import CompanyCreate, CompanyUpdate, CompanyRead
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
    "ContactCreate",
    "ContactUpdate",
    "ContactRead",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyRead",
    "PipelineCreate",
    "PipelineUpdate",
    "PipelineRead",
    "PipelineStageCreate",
    "PipelineStageUpdate",
    "PipelineStageRead",
    "DealCreate",
    "DealUpdate",
    "DealRead",
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityRead",
    "ListCreate",
    "ListUpdate",
    "ListRead",
    "ListMembershipCreate",
    "ListMembershipRead",
    "AssociationCreate",
    "AssociationRead",
]