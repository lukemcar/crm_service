"""
Centralised JSON logging for the Dyno CRM microservice.

This module configures Python’s :mod:`logging` module to emit
structured JSON log lines enriched with OpenTelemetry trace context
and correlation identifiers.  The configuration is applied once on
application and worker startup via the :func:`configure_logging`
function.  A small helper :func:`get_logger` returns a named logger
within the configured logging hierarchy.  The implementation is
modelled after the logging used in other Dyno services (e.g. the
formless agent) to ensure consistency across microservices.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

try:
    # Attempt to import OpenTelemetry context API.  If unavailable,
    # tracing fields will be omitted from logs.
    from opentelemetry import trace  # type: ignore
except Exception:
    trace = None  # type: ignore


class JsonLogFormatter(logging.Formatter):
    """Custom log formatter that emits structured JSON.

    Each log record is serialised to a JSON object with at least the
    following fields:

      - ``timestamp``: ISO 8601 timestamp with UTC timezone
      - ``level``: log level name
      - ``name``: logger name
      - ``message``: formatted message
      - ``trace_id``: current OpenTelemetry trace id (hex), if available
      - ``span_id``: current span id (hex), if available
      - ``correlation_id``: a user-defined correlation id if supplied on
        the record (set via logger.bind or ``extra`` dict)
      - ``tenant_id``: the tenant identifier if supplied on the record
      - ``user_id``: the acting user identifier if supplied on the record

    Additional attributes attached to the record via ``extra`` will be
    preserved in the JSON output.  This formatter never raises an
    exception; on failure to serialise, it falls back to returning a
    minimal JSON payload containing only the log message.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {}
        # Timestamp in ISO 8601 with UTC timezone
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        log_record["level"] = record.levelname
        log_record["name"] = record.name
        log_record["message"] = record.getMessage()
        # Trace context
        if trace is not None:
            span = trace.get_current_span()
            ctx = span.get_span_context() if span is not None else None
            if ctx and getattr(ctx, "trace_id", 0) != 0:
                # format trace_id and span_id as 32/16 hex digits
                log_record["trace_id"] = format(ctx.trace_id, "032x")
                log_record["span_id"] = format(ctx.span_id, "016x")
        # Correlation identifiers (if provided via logger.extra)
        for key in ("correlation_id", "tenant_id", "user_id"):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)
        # Preserve any user-defined extras; avoid overwriting known keys
        for key, value in record.__dict__.items():
            if key not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                if key not in log_record:
                    log_record[key] = value
        # Serialise to JSON; fallback on failure
        try:
            return json.dumps(log_record, default=str)
        except Exception:
            return json.dumps({"message": record.getMessage()})


def configure_logging() -> logging.Logger:
    """Configure the root logger for JSON output.

    This function initialises the global logging configuration once.  The
    log level is derived from the ``LOG_LEVEL`` environment variable (default
    ``INFO``).  A single stream handler is attached to the root logger
    with our custom JSON formatter.  Subsequent calls return the same
    named logger without reconfiguring the root.

    Returns:
        A named logger for the CRM application.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_str, logging.INFO)
    root_logger = logging.getLogger()
    # Only configure handlers once to avoid duplicate logs
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonLogFormatter()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)
    # Return a dedicated application logger
    return logging.getLogger("crm")


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of the CRM logger.

    Args:
        name: The name of the logger (module or component name).

    Returns:
        A :class:`logging.Logger` instance.
    """
    return logging.getLogger(f"crm.{name}")
