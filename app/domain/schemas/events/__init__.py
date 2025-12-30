"""
Aggregate exports for event schemas.

This package contains Pydantic models representing the payload
structures for events emitted by the CRM.  Importing from this
module simplifies usage by exposing the most commonly used classes
from each underlying module.
"""

from .common import EventEnvelope
from .contact_event import (
    ContactCreatedEvent,
    ContactUpdatedEvent,
    ContactDeletedEvent,
    ContactDelta,
)
from .company_event import (
    CompanyCreatedEvent,
    CompanyUpdatedEvent,
    CompanyDeletedEvent,
    CompanyDelta,
)
from .pipeline_event import (
    PipelineBaseMessage,
    PipelineCreatedMessage,
    PipelineUpdatedMessage,
    PipelineDeletedMessage,
)
from .pipeline_stage_event import (
    PipelineStageBaseMessage,
    PipelineStageCreatedMessage,
    PipelineStageUpdatedMessage,
    PipelineStageDeletedMessage,
)
from .deal_event import (
    DealBaseMessage,
    DealCreatedMessage,
    DealUpdatedMessage,
    DealDeletedMessage,
)
from .activity_event import (
    ActivityBaseMessage,
    ActivityCreatedMessage,
    ActivityUpdatedMessage,
    ActivityDeletedMessage,
)
from .list_event import (
    ListBaseMessage,
    ListCreatedMessage,
    ListUpdatedMessage,
    ListDeletedMessage,
)
from .list_membership_event import (
    ListMembershipBaseMessage,
    ListMembershipCreatedMessage,
    ListMembershipDeletedMessage,
)
from .association_event import (
    AssociationBaseMessage,
    AssociationCreatedMessage,
    AssociationDeletedMessage,
)

__all__ = [
    # Common envelope
    "EventEnvelope",
    # Contacts
    "ContactCreatedEvent",
    "ContactUpdatedEvent",
    "ContactDeletedEvent",
    "ContactDelta",
    # Companies
    "CompanyCreatedEvent",
    "CompanyUpdatedEvent",
    "CompanyDeletedEvent",
    "CompanyDelta",
    # Pipelines
    "PipelineBaseMessage",
    "PipelineCreatedMessage",
    "PipelineUpdatedMessage",
    "PipelineDeletedMessage",
    # Pipeline stages
    "PipelineStageBaseMessage",
    "PipelineStageCreatedMessage",
    "PipelineStageUpdatedMessage",
    "PipelineStageDeletedMessage",
    # Deals
    "DealBaseMessage",
    "DealCreatedMessage",
    "DealUpdatedMessage",
    "DealDeletedMessage",
    # Activities
    "ActivityBaseMessage",
    "ActivityCreatedMessage",
    "ActivityUpdatedMessage",
    "ActivityDeletedMessage",
    # Lists
    "ListBaseMessage",
    "ListCreatedMessage",
    "ListUpdatedMessage",
    "ListDeletedMessage",
    # List memberships
    "ListMembershipBaseMessage",
    "ListMembershipCreatedMessage",
    "ListMembershipDeletedMessage",
    # Associations
    "AssociationBaseMessage",
    "AssociationCreatedMessage",
    "AssociationDeletedMessage",
]