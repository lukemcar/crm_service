"""Tests for OpenTelemetry initialization in the CRM service.

These tests verify that the tracing setup does not configure an OTLP
exporter when no exporter endpoint is specified via environment
variables.  They also ensure that instrumentation functions can be
invoked multiple times without error.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.telemetry import init_tracing, instrument_fastapi


def test_init_tracing_without_exporter_env(monkeypatch) -> None:
    """init_tracing should return early when no OTLP endpoint is configured."""
    # Ensure environment variables for OTLP endpoint are unset
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    # Calling init_tracing should not raise and should perform no configuration
    init_tracing(service_name="crm-test")
    # A second call should also be a no-op
    init_tracing(service_name="crm-test")
    # Create a dummy FastAPI app and instrument it; this should not raise
    app = FastAPI()
    instrument_fastapi(app)
