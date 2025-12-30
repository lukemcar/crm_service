"""Celery application configuration for the DYNO CRM service.

This module defines a Celery application and routing configuration
tailored to the CRM domain.  It follows the conventions used in
the tenant management service but replaces the exchange name and
queue layout with CRM‑specific values.  Each domain entity (contact,
company, etc.) has its own queue and dead‑letter queue to isolate
failures and allow targeted retry policies.  Tasks are routed
according to their fully qualified name (e.g. ``crm.contact.created``).

The Celery application is intended to be shared by producers and
consumers within the CRM service.  Producers import the
``EXCHANGE_NAME`` constant to build their task names and call
``send_task`` via the BaseProducer helper.
"""

from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import Config
from app.core.telemetry import init_tracing, instrument_celery


# Instantiate a single Celery application for the CRM service.  The
# application name is arbitrary but should be unique within the
# process space.  Using a descriptive name aids in debugging.
celery_app = Celery("dyno_crm_service")


# --------------------------------------------------------------------
# Core broker / backend configuration
# --------------------------------------------------------------------
# All CRM tasks are serialized as JSON for safety and interoperability.
celery_app.conf.update(
    broker_url=Config.celery_broker_url(),
    result_backend=Config.celery_result_backend(),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    timezone="UTC",
    broker_connection_retry_on_startup=True,
)

# Name of the exchange used by the CRM service.  All task names are
# prefixed with this value.  Producers construct their task names
# using this constant to ensure consistency with the routing table.
EXCHANGE_NAME: str = "crm"


# --------------------------------------------------------------------
# Exchanges and queues
# --------------------------------------------------------------------
# Define a single topic exchange for all CRM domain events.  A topic
# exchange allows routing by pattern using the task name as the
# routing key.
crm_exchange = Exchange(EXCHANGE_NAME, type="topic")

# Define a dead‑letter exchange (DLX) for CRM.  Messages that fail
# processing after exhausting retries are routed to this exchange.
crm_dlx = Exchange(f"{EXCHANGE_NAME}.dlx", type="topic")

# Configure Celery defaults to use the CRM exchange.  Tasks that do
# not specify a route explicitly will be sent to the default queue.
celery_app.conf.task_default_exchange = crm_exchange.name
celery_app.conf.task_default_exchange_type = crm_exchange.type
celery_app.conf.task_default_routing_key = f"{EXCHANGE_NAME}.default"

# Build a list of domains used by the CRM service.  Each domain will
# have its own primary queue and a corresponding dead‑letter queue.
_domains = [
    "contact",
    "company",
    "company_relationship",
    "contact_company_relationship",
    "lead",
    "pipeline",
    "pipeline_stage",
    "deal",
    "activity",
    "list",
    "list_membership",
    "association",
]

# Start with the default queue for tasks that lack an explicit route.
task_queues: list[Queue] = [
    Queue(
        f"{EXCHANGE_NAME}.default",
        exchange=crm_exchange,
        routing_key=f"{EXCHANGE_NAME}.default",
    ),
]

# Append a queue for each domain and its dead‑letter queue.  Messages
# published to ``{EXCHANGE_NAME}.{domain}.*`` will be routed to the
# corresponding domain queue.  Failed messages are re‑routed to the
# DLQ with the same domain prefix.
for _domain in _domains:
    # Primary queue for the domain
    task_queues.append(
        Queue(
            f"{EXCHANGE_NAME}.{_domain}",
            exchange=crm_exchange,
            routing_key=f"{EXCHANGE_NAME}.{_domain}.#",
            queue_arguments={
                "x-dead-letter-exchange": crm_dlx.name,
                "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.{_domain}.dlq",
            },
        )
    )
    # Dead letter queue for the domain
    task_queues.append(
        Queue(
            f"{EXCHANGE_NAME}.{_domain}.dlq",
            exchange=crm_dlx,
            routing_key=f"{EXCHANGE_NAME}.{_domain}.dlq",
        )
    )

celery_app.conf.task_queues = tuple(task_queues)


# --------------------------------------------------------------------
# Task routing
# --------------------------------------------------------------------
# Map known task names to queues and routing keys.  Each CRUD action
# for every domain is explicitly routed to the domain queue.  This
# prevents tasks from being sent to the default queue and ensures
# proper isolation.  If additional task patterns are introduced,
# expand this mapping accordingly.
task_routes: dict[str, dict[str, str]] = {}
for _domain in _domains:
    for _action in ("created", "updated", "deleted"):
        task_name = f"{EXCHANGE_NAME}.{_domain}.{_action}"
        task_routes[task_name] = {
            "queue": f"{EXCHANGE_NAME}.{_domain}",
            "routing_key": task_name,
        }

celery_app.conf.task_routes = task_routes


# --------------------------------------------------------------------
# Task discovery for consumers
# --------------------------------------------------------------------
# Autodiscover any Celery tasks defined in the ``app.messaging.tasks``
# package.  Consumers should define tasks in this package so that the
# worker can find and register them automatically.  Producers do not
# need to be discovered.
celery_app.autodiscover_tasks([
    "app.messaging.tasks",
])


# --------------------------------------------------------------------
# Telemetry integration
# --------------------------------------------------------------------
# Initialise tracing and instrument Celery for OpenTelemetry support.
# These calls are no‑ops if tracing is not configured in the
# environment.  Errors during instrumentation are suppressed to avoid
# impacting the application startup.
try:
    init_tracing(service_name=f"{EXCHANGE_NAME}.worker")
    instrument_celery(celery_app)
    # Instrument httpx globally for Celery worker processes
    from app.core.telemetry import instrument_httpx

    instrument_httpx()
except Exception:
    # Telemetry may not be available; ignore errors
    pass
