"""
OpenTelemetry instrumentation for the Dyno CRM service.

This module configures distributed tracing for both the FastAPI
application and Celery background workers.  When OpenTelemetry
instrumentation packages are available they are initialised; otherwise,
the functions perform no-op.  The tracer uses an OTLP exporter by
default and can be configured via environment variables
(``OTEL_EXPORTER_OTLP_ENDPOINT``, ``OTEL_EXPORTER_OTLP_HEADERS``, etc.).

The implementation is adapted from the Tenant Management Service and
other Dyno services to provide consistent tracing behaviour across the
platform.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

try:
    # Attempt to import OpenTelemetry SDK and instrumentation
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
except Exception:
    # If OpenTelemetry packages are unavailable, set to None to disable instrumentation
    trace = None  # type: ignore
    FastAPIInstrumentor = None  # type: ignore
    CeleryInstrumentor = None  # type: ignore
    HTTPXClientInstrumentor = None  # type: ignore
    SQLAlchemyInstrumentor = None  # type: ignore

logger = logging.getLogger(__name__)


def init_tracing(service_name: str = "crm") -> None:
    """Initialise OpenTelemetry tracing for the CRM service.

    When the OpenTelemetry packages are unavailable this function logs a
    message and returns immediately.  Otherwise, a global tracer
    provider with an OTLP exporter is configured.  The service name
    may be overridden via the ``OTEL_SERVICE_NAME`` environment
    variable (a standard OpenTelemetry convention).

    Args:
        service_name: The default service name to register with the tracer.
    """
    if trace is None:
        logger.info("OpenTelemetry not available; tracing disabled")
        return
    # Only configure once: avoid reconfiguring if a real tracer provider exists
    from opentelemetry.sdk.trace import TracerProvider as _TP
    if isinstance(trace.get_tracer_provider(), _TP):
        return
    import os
    env_service_name = os.getenv("OTEL_SERVICE_NAME")
    chosen_service_name = env_service_name or service_name
    # If no OTLP endpoint is configured, disable tracing.
    # Without this guard, the default OTLP exporter will attempt to
    # connect to localhost:4318 and emit errors when no collector is running.
    exporter_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not exporter_endpoint:
        logger.info(
            "OTEL exporter endpoint not configured; tracing disabled (set OTEL_EXPORTER_OTLP_ENDPOINT to enable)"
        )
        return
    # Merge default and custom resources
    default_resource = Resource.create()
    custom_resource = Resource.create({"service.name": chosen_service_name})
    resource = default_resource.merge(custom_resource)
    provider = TracerProvider(resource=resource)
    # Configure OTLP exporter
    exporter: Optional[Any] = None
    try:
        exporter = OTLPSpanExporter()
    except Exception:
        logger.warning("Failed to create OTLP exporter; tracing disabled")
        return
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry tracing configured for service '%s'", chosen_service_name)


def instrument_fastapi(app: Any) -> None:
    """Instrument a FastAPI application for tracing.

    Should be called after initialising tracing.  If instrumentation is
    unavailable, logs a warning.  FastAPIInstrumentor will wrap
    routes so that incoming requests start new spans automatically.

    Args:
        app: The FastAPI application instance to instrument.
    """
    if FastAPIInstrumentor is None:
        logger.warning("FastAPI instrumentation not available; skipping")
        return
    try:
        FastAPIInstrumentor().instrument_app(app, tracer_provider=trace.get_tracer_provider())
        logger.info("FastAPI application instrumented for tracing")
    except Exception:
        logger.exception("Failed to instrument FastAPI; tracing disabled for API")


def instrument_celery(celery_app: Any) -> None:
    """Instrument a Celery application for tracing.

    When the Celery instrumentation package is available, tasks will
    automatically propagate context and create spans around task
    execution.  Otherwise, this function logs and returns.

    Args:
        celery_app: The Celery application instance to instrument.
    """
    if CeleryInstrumentor is None:
        logger.warning("Celery instrumentation not available; skipping")
        return
    try:
        CeleryInstrumentor().instrument()
        logger.info("Celery instrumented for tracing")
    except Exception:
        logger.exception("Failed to instrument Celery; tracing disabled for tasks")


def instrument_httpx() -> None:
    """Instrument httpx clients globally for tracing.

    If the httpx instrumentation package is available, calling this
    function will ensure that all httpx.Client and AsyncClient
    instances automatically create spans for outbound requests.  If
    instrumentation is unavailable, logs and returns without raising
    an exception.
    """
    if HTTPXClientInstrumentor is None:
        logger.warning("httpx instrumentation not available; skipping")
        return
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx globally instrumented for tracing")
    except Exception:
        logger.exception("Failed to instrument httpx; tracing for HTTP disabled")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument a SQLAlchemy engine for tracing.

    This helper wraps SQLAlchemy's execution engine so that each
    database query emits a span.  It must be called after the engine
    is created.  If instrumentation is unavailable or tracing is
    disabled, the function logs and returns without error.

    Args:
        engine: The SQLAlchemy engine instance to instrument.
    """
    if SQLAlchemyInstrumentor is None:
        logger.warning("SQLAlchemy instrumentation not available; skipping")
        return
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy engine instrumented for tracing")
    except Exception:
        logger.exception("Failed to instrument SQLAlchemy engine; tracing disabled for DB")


def attach_current_span_context(
    *, tenant_id: Optional[str] = None, correlation_id: Optional[str] = None, message_id: Optional[str] = None
) -> None:
    """Attach correlation identifiers to the current active span.

    This helper reads the current span from the tracer provider and
    attaches custom attributes for tenant, correlation and message IDs
    if a span is active.  It should be called after setting the
    correlation/message IDs via the correlation utilities.  If no span
    is active or tracing is disabled, the function is a no-op.

    Args:
        tenant_id: The tenant identifier associated with the operation.
        correlation_id: The current correlation ID.
        message_id: The current message (causation) ID.
    """
    try:
        if trace is None:
            return
        span = trace.get_current_span()
        # Only attach attributes if there is an active span (not NoOp span)
        if span and hasattr(span, "set_attribute"):
            if tenant_id:
                span.set_attribute("dyno.tenant_id", tenant_id)
            if correlation_id:
                span.set_attribute("dyno.correlation_id", correlation_id)
            if message_id:
                span.set_attribute("dyno.message_id", message_id)
    except Exception:
        # Never raise from context attachment
        logger.debug("Could not attach context to span", exc_info=True)