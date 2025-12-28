"""
Common producer utilities for DYNO CRM events.

This module defines a ``BaseProducer`` class that can be used by
specialised producers to send domain events.  Each event is
wrapped in an ``EventEnvelope`` from ``app.domain.schemas.events`` and
contains metadata such as a unique event identifier and tenant
information.  In a production environment the ``emit`` method would
publish the envelope to a message broker (e.g. RabbitMQ).  In this
reference implementation the envelope is simply logged to STDOUT,
providing a placeholder for future broker integration.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Type
from uuid import uuid4

from app.domain.schemas.events import EventEnvelope


class BaseProducer:
    """Base class for all domain event producers.

    Subclasses should define high level helper methods (e.g.
    ``contact_created``) that build an appropriate message model and
    invoke ``_send`` with a routing key / task name.  The base class
    handles wrapping the domain message in an ``EventEnvelope`` and
    serialising it to JSON.  Downstream services can deserialize the
    envelope and inspect the ``event_type`` to route the message to
    appropriate handlers.
    """

    # Name of the producing service.  Used to populate the
    # ``producer`` field on the EventEnvelope.  Subclasses can
    # override this if necessary.
    PRODUCER_NAME: str = "dy_crm_service"

    @classmethod
    def _send(
        cls,
        *,
        task_name: str,
        message_model: Any,
        headers: Dict[str, str] | None = None,
    ) -> None:
        """Wrap the message in an envelope and emit it.

        Args:
            task_name: Routing key / task name indicating the type of
                event (e.g. ``crm.contact.created``).
            message_model: An instance of a Pydantic model representing
                the domain payload.  Must have a ``tenant_id`` field.
            headers: Optional dictionary of additional headers.  This
                implementation does not currently use headers, but
                accepts them for compatibility with future broker
                integrations.
        """
        # Convert the domain model to a JSON‑serialisable dict
        payload: Dict[str, Any] = message_model.model_dump(mode="json")
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type=task_name,
            schema_version=1,
            occurred_at=datetime.utcnow(),
            producer=cls.PRODUCER_NAME,
            tenant_id=message_model.tenant_id,
            correlation_id=None,
            causation_id=None,
            traceparent=None,
            data=payload,
        )
        # Serialize envelope to JSON for emission
        serialized = envelope.model_dump(mode="json")
        # Emit the event.  In this reference implementation we simply
        # print the JSON to STDOUT.  In a real system this would
        # publish to RabbitMQ or another message broker.
        cls.emit(serialized, headers or {})

    @staticmethod
    def emit(envelope_dict: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Emit the envelope to the output channel.

        Override this method to integrate with a message broker.  The
        default implementation prints the event envelope as a JSON
        string, prefixed with the event_type for easy identification.

        Args:
            envelope_dict: The envelope serialised to a dictionary.
            headers: Optional headers to include when emitting the
                message.  Currently unused.
        """
        event_type = envelope_dict.get("event_type")
        json_payload = json.dumps(envelope_dict, default=str)
        print(f"[EVENT] {event_type}: {json_payload}")
