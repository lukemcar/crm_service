"""
Generic event consumers for DYNO CRM.

This module defines minimalistic consumer functions for handling CRM
events.  The functions are designed to be called with the
deserialised event envelope (a ``dict``) as produced by
``BaseProducer``.  Real implementations should call into the
application services to perform side effects (e.g. updating the
database).  These consumers currently just log the event data and
return, serving as stubs for future development.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

import json


def process_contact_created(envelope: Dict[str, Any]) -> None:
    """Handle a contact.created event.

    Args:
        envelope: The event envelope as a dictionary.
    """
    data = envelope.get("data", {})
    print(f"[CONSUMER] Process contact created: {json.dumps(data, default=str)}")


def process_contact_updated(envelope: Dict[str, Any]) -> None:
    """Handle a contact.updated event."""
    data = envelope.get("data", {})
    print(f"[CONSUMER] Process contact updated: {json.dumps(data, default=str)}")


def process_contact_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a contact.deleted event."""
    data = envelope.get("data", {})
    print(f"[CONSUMER] Process contact deleted: {json.dumps(data, default=str)}")


# Mapping of event routing keys to handler functions.  Extend this
# dictionary to support new events.
EVENT_HANDLERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "crm.contact.created": process_contact_created,
    "crm.contact.updated": process_contact_updated,
    "crm.contact.deleted": process_contact_deleted,
}


def consume_event(envelope: Dict[str, Any]) -> None:
    """Route an event to the appropriate handler.

    Args:
        envelope: The deserialised event envelope.
    """
    event_type = envelope.get("event_type")
    handler = EVENT_HANDLERS.get(event_type)
    if handler is None:
        print(f"[CONSUMER] No handler for event_type={event_type}")
        return
    handler(envelope)
