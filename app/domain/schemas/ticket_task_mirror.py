"""
Pydantic schemas for TicketTaskMirror.

These models define request and response structures for managing
mirrored tasks associated with support tickets. Ticket task mirrors
represent Flowable tasks mirrored in CRM to display assignments and
status without querying the orchestration engine. These tasks are
generally read-only for tenants. Admin or internal APIs may upsert
records to recover from missed events or to seed initial data.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TicketTaskMirrorBase(BaseModel):
    """Shared attributes for a ticket task mirror upsert."""

    ticket_id: uuid.UUID = Field(
        ..., description="Identifier of the ticket this task belongs to"
    )
    orchestration_task_id: str = Field(
        ..., max_length=128, description="Task identifier from the orchestration engine"
    )
    orchestration_process_instance_id: Optional[str] = Field(
        default=None, max_length=128, description="Process instance identifier from Flowable"
    )
    orchestration_process_definition_key: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Process definition key from Flowable for this task",
    )
    name: str = Field(
        ..., max_length=255, description="Display name of the task"
    )
    description: Optional[str] = Field(
        default=None, description="Optional description of the task"
    )
    status: Optional[str] = Field(
        default="open", max_length=50, description="Status of the task"
    )
    due_at: Optional[str] = Field(
        default=None,
        description="Due date/time for the task in ISO 8601 format; nullable",
    )
    assigned_user_id: Optional[uuid.UUID] = Field(
        default=None, description="User assigned to this task"
    )
    assigned_group_id: Optional[uuid.UUID] = Field(
        default=None, description="Group assigned to this task"
    )


class AdminUpsertTicketTaskMirror(TicketTaskMirrorBase):
    """Request model for upserting a ticket task mirror via the admin API."""

    tenant_id: uuid.UUID = Field(
        ..., description="Tenant identifier for the task mirror"
    )
    id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "Unique identifier for the task mirror. "
            "If omitted, a new record will be created."
        ),
    )


class TicketTaskMirrorOut(BaseModel):
    """Response model representing a ticket task mirror."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    orchestration_task_id: str
    orchestration_process_instance_id: Optional[str] = None
    orchestration_process_definition_key: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: str
    due_at: Optional[str] = None
    assigned_user_id: Optional[uuid.UUID] = None
    assigned_group_id: Optional[uuid.UUID] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


__all__ = [
    "TicketTaskMirrorBase",
    "AdminUpsertTicketTaskMirror",
    "TicketTaskMirrorOut",
]