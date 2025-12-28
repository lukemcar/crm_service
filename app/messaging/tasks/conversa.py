"""Consumers for Dyno Conversa (Formless Agent) events.

This module defines stub handlers for events emitted by the Dyno
Conversa service (formless agent).  Real implementations should parse
the event payloads, perform upserts into the CRM database (e.g.
creating or updating contacts or leads) and publish follow-on CRM
events as needed.  For now, these handlers simply log the incoming
event data to stdout.

The routing keys used here follow the conventions described in the
Conversa Integration Guide, such as ``conversa.form-session.completed``
for form completion events and ``conversa.engagement.updated`` for
identity updates.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

import json


def process_form_session_completed(envelope: Dict[str, Any]) -> None:
    """Handle a form-session.completed event.

    In a full implementation, this handler would extract the form
    responses from the payload, resolve or create a CRM contact/lead
    based on the engagement identity, and possibly trigger follow-up
    actions.  Here we just log the data.

    Args:
        envelope: The event envelope as a dictionary.
    """
    data = envelope.get("data", {})
    print(f"[CONVERSA] Form session completed: {json.dumps(data, default=str)}")


def process_engagement_updated(envelope: Dict[str, Any]) -> None:
    """Handle an engagement.updated event.

    This event indicates that identity information for an engagement
    has changed (e.g., a new email or phone number was provided).  A
    real implementation would update the corresponding CRM contact if
    one exists.  Here we simply log the payload.
    """
    data = envelope.get("data", {})
    print(f"[CONVERSA] Engagement updated: {json.dumps(data, default=str)}")


def process_form_template_created(envelope: Dict[str, Any]) -> None:
    """Handle a form-template.created event (placeholder)."""
    data = envelope.get("data", {})
    print(f"[CONVERSA] Form template created: {json.dumps(data, default=str)}")


def process_unknown(envelope: Dict[str, Any]) -> None:
    """Fallback handler for unrecognised Conversa events."""
    print(f"[CONVERSA] Unhandled event_type={envelope.get('event_type')}")


# Mapping of Conversa event types to handler functions
CONVERSA_EVENT_HANDLERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "conversa.form-session.completed": process_form_session_completed,
    "conversa.engagement.updated": process_engagement_updated,
    "conversa.form-template.created": process_form_template_created,
}


def consume_conversa_event(envelope: Dict[str, Any]) -> None:
    """Route a Conversa event to the appropriate handler.

    This dispatcher looks up the handler based on the ``event_type``
    field of the envelope.  If no handler exists for the given type,
    :func:`process_unknown` is invoked.

    Args:
        envelope: The deserialised event envelope from Conversa.
    """
    event_type = envelope.get("event_type")
    handler = CONVERSA_EVENT_HANDLERS.get(event_type, process_unknown)
    handler(envelope)