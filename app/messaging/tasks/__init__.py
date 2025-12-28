"""
Asynchronous event consumers for the CRM service.

This package contains simple consumer functions that can be hooked into
a message processing loop.  When an event is received from the
message broker, it should be deserialised into a dictionary and
passed to ``consume_event``.  The function will route the event to
the appropriate handler based on its ``event_type`` field.  Handlers
defined here currently log the event data; in a production
deployment they would invoke domain services to apply state changes.
"""

from .consumers import (
    consume_event,
    process_contact_created,
    process_contact_updated,
    process_contact_deleted,
)
from .conversa import consume_conversa_event, process_form_session_completed, process_engagement_updated
from .tenant import (
    consume_tenant_event,
    process_tenant_created,
    process_tenant_updated,
    process_tenant_deleted,
    process_tenant_user_created,
    process_tenant_user_updated,
    process_tenant_user_deleted,
    process_role_created,
    process_role_updated,
    process_role_deleted,
    process_group_created,
    process_group_updated,
    process_group_deleted,
    process_role_assignment_created,
    process_role_assignment_deleted,
    process_group_assignment_created,
    process_group_assignment_deleted,
)
from .orchestration import (
    consume_orchestration_event,
    process_task_created,
    process_task_assigned,
    process_task_completed,
    process_task_updated,
    process_task_deleted,
)
from .orchestration import consume_orchestration_event, process_task_created, process_task_assigned, process_task_completed, process_task_updated, process_task_deleted

__all__ = [
    "consume_event",
    "process_contact_created",
    "process_contact_updated",
    "process_contact_deleted",
    "consume_conversa_event",
    "process_form_session_completed",
    "process_engagement_updated",
    "consume_tenant_event",
    "process_tenant_created",
    "process_tenant_updated",
    "process_tenant_deleted",
    "process_tenant_user_created",
    "process_tenant_user_updated",
    "process_tenant_user_deleted",
    "process_role_created",
    "process_role_updated",
    "process_role_deleted",
    "process_group_created",
    "process_group_updated",
    "process_group_deleted",
    "process_role_assignment_created",
    "process_role_assignment_deleted",
    "process_group_assignment_created",
    "process_group_assignment_deleted",
    "consume_orchestration_event",
    "process_task_created",
    "process_task_assigned",
    "process_task_completed",
    "process_task_updated",
    "process_task_deleted",
]