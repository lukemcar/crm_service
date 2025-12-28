"""
Common event envelope definitions for DYNO CRM messaging.

All events published by the CRM service should be wrapped in an
``EventEnvelope``.  The envelope captures metadata such as a unique
``event_id``, the ``event_type`` (routing key for this event),
the schema version of the payload, and identifiers used for tracing
across systems.  The actual domain payload is stored in the ``data``
field.  Consumers can inspect the envelope to perform idempotency
checks and correlate events.

The structure closely follows the patterns used by other Dyno
services (e.g. tenant management, formless agent) but does not
assume the presence of Celery or any particular broker.  Producers
are free to serialise the envelope to JSON and deliver it over
RabbitMQ or another transport.  Consumers should always validate
the ``event_type`` and ``schema_version`` before processing the
embedded payload.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Standard wrapper for all CRM events.

    An ``EventEnvelope`` contains metadata about an event as well as
    the domain payload.  The ``event_id`` uniquely identifies the
    envelope and should be used for idempotency checks.  The
    ``event_type`` determines which consumer should handle the event.
    The ``producer`` field identifies the source service.  The
    ``tenant_id`` allows consumers to scope processing to the
    appropriate tenant.  The ``correlation_id`` and ``causation_id``
    fields can be used to track chains of events but may be omitted
    by simple producers.  The ``traceparent`` field is reserved for
    future OpenTelemetry propagation.
    """

    event_id: UUID = Field(..., description="Unique identifier for this event")
    event_type: str = Field(..., description="Routing key / task name for this event")
    schema_version: int = Field(1, description="Version of the event payload schema")
    occurred_at: datetime = Field(..., description="UTC timestamp when the event occurred")
    producer: str = Field(..., description="Name of the producing service")
    tenant_id: UUID = Field(..., description="Tenant identifier")
    correlation_id: Optional[Union[UUID, str]] = Field(
        None,
        description="Correlation identifier linking a chain of events",
    )
    causation_id: Optional[Union[UUID, str]] = Field(
        None, description="Identifier of the event that directly triggered this event"
    )
    traceparent: Optional[str] = Field(
        None, description="W3C traceparent header for distributed tracing"
    )
    data: Dict[str, Any] = Field(..., description="Domain payload for the event")

    class Config:
        orm_mode = True
