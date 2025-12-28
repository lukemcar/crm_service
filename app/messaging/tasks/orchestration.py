"""Consumers for Orchestration (Flowable BPM) task events.

This module defines placeholder handlers for events emitted by the
Dyno Orchestration service, which is built on a BPMN engine such as
Flowable.  The CRM uses these events to mirror human tasks into
its own task list and to allow users to claim or complete tasks
from within the CRM UI.  Real implementations would upsert records
into a ``workflow_tasks`` table and possibly trigger notifications.

The routing keys follow the pattern described in the integration
guide, such as ``orchestration.task.created`` when a new task
appears and ``orchestration.task.completed`` when a task has
finished.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

import json


def process_task_created(envelope: Dict[str, Any]) -> None:
    """Handle a task.created event.

    Args:
        envelope: The event envelope as a dictionary.
    """
    data = envelope.get("data", {})
    print(f"[ORCHESTRATION] Task created: {json.dumps(data, default=str)}")


def process_task_assigned(envelope: Dict[str, Any]) -> None:
    """Handle a task.assigned event.

    This event indicates that a task has been claimed or assigned
    to a user.  The payload typically includes the assignee ID.
    """
    data = envelope.get("data", {})
    print(f"[ORCHESTRATION] Task assigned: {json.dumps(data, default=str)}")


def process_task_completed(envelope: Dict[str, Any]) -> None:
    """Handle a task.completed event."""
    data = envelope.get("data", {})
    print(f"[ORCHESTRATION] Task completed: {json.dumps(data, default=str)}")


def process_task_updated(envelope: Dict[str, Any]) -> None:
    """Handle a task.updated event."""
    data = envelope.get("data", {})
    print(f"[ORCHESTRATION] Task updated: {json.dumps(data, default=str)}")


def process_task_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a task.deleted event."""
    data = envelope.get("data", {})
    print(f"[ORCHESTRATION] Task deleted: {json.dumps(data, default=str)}")


def process_unknown(envelope: Dict[str, Any]) -> None:
    """Fallback handler for unrecognised orchestration events."""
    print(f"[ORCHESTRATION] Unhandled event_type={envelope.get('event_type')}")


# Mapping of orchestration event types to handler functions.  Extend
# this dictionary to support additional events.
ORCHESTRATION_EVENT_HANDLERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "orchestration.task.created": process_task_created,
    "orchestration.task.assigned": process_task_assigned,
    "orchestration.task.completed": process_task_completed,
    "orchestration.task.updated": process_task_updated,
    "orchestration.task.deleted": process_task_deleted,
}


def consume_orchestration_event(envelope: Dict[str, Any]) -> None:
    """Route an orchestration event to the appropriate handler.

    Args:
        envelope: The deserialised event envelope from the Orchestration service.
    """
    event_type = envelope.get("event_type")
    handler = ORCHESTRATION_EVENT_HANDLERS.get(event_type, process_unknown)
    handler(envelope)