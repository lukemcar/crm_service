# app/core/celery_app.py
from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import Config
from app.core.telemetry import init_tracing, instrument_celery


# Single, shared Celery application for the whole service
celery_app = Celery("tenant_management_service")



# --------------------------------------------------------------------
# Core broker / backend config (RabbitMQ 4.2.1, JSON only, no pickle)
# --------------------------------------------------------------------
celery_app.conf.update(
    broker_url=Config.celery_broker_url(),
    result_backend=Config.celery_result_backend(),

    # Safety & interoperability
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    timezone="UTC",

    # Retry connecting to broker on startup (good with RabbitMQ restarts)
    broker_connection_retry_on_startup=True,
)

EXCHANGE_NAME = "tenant_mngr_srv"

# --------------------------------------------------------------------
# Exchanges, queues, and routing
# --------------------------------------------------------------------
# Use a single topic exchange for all Dyno tenant_mngr_srv domain events.  The legacy
# ``formless_agent`` exchange and related queues/routes were removed to
# simplify the messaging topology.  See CHANGELOG for details.
tenant_mngr_srv_exchange = Exchange(EXCHANGE_NAME, type="topic")

# Dead letter exchange for all tenant_mngr_srv queues.  Messages routed
# to this exchange when retries are exhausted or a consumer rejects
# a message.  The DLX is a separate topic exchange to keep
# dead-letter traffic isolated from primary queues.
tenant_mngr_srv_dlx = Exchange(f"{EXCHANGE_NAME}.dlx", type="topic")

# Set Celery defaults to the tenant_mngr_srv exchange.  Most tasks specify their
# own routing key and queue via ``task_routes`` below.  The default queue is
# used as a catch-all for tasks that are not explicitly routed.
celery_app.conf.task_default_exchange = tenant_mngr_srv_exchange.name
celery_app.conf.task_default_exchange_type = tenant_mngr_srv_exchange.type
celery_app.conf.task_default_routing_key = f"{EXCHANGE_NAME}.default"

celery_app.conf.task_queues = (
    # Generic catch-all for tasks without a more specific queue
    Queue(
        f"{EXCHANGE_NAME}.default",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.default",
    ),
    # Form session lifecycle events (replaces formless_agent.form_session)
    Queue(
        f"{EXCHANGE_NAME}.tenant",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant.#",
        queue_arguments={
            # route messages that fail or exhaust retries to the DLQ
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant.dlq",
        },
    ),
)

# Append dead-letter queues to the queue list.  These queues collect
# messages that have failed processing and exhausted their retries.
celery_app.conf.task_queues += (
    Queue(
        f"{EXCHANGE_NAME}.tenant.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant.dlq",
    ),
)

# --------------------------------------------------------------------
# Additional queues for other domain events
# Each domain object has its own queue and a corresponding dead-letter queue
# to isolate failures and allow targeted retry policies.  Routing keys
# are namespaced under the tenant_mngr_srv exchange.
celery_app.conf.task_queues += (
    # Tenant user events
    Queue(
        f"{EXCHANGE_NAME}.tenant_user",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant_user.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant_user.dlq",
        },
    ),
    # Tenant role events
    Queue(
        f"{EXCHANGE_NAME}.tenant_role",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant_role.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant_role.dlq",
        },
    ),
    # Tenant group events
    Queue(
        f"{EXCHANGE_NAME}.tenant_group",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant_group.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant_group.dlq",
        },
    ),
    # Tenant role assignment events
    Queue(
        f"{EXCHANGE_NAME}.tenant_role_assignment",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant_role_assignment.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant_role_assignment.dlq",
        },
    ),
    # Tenant group assignment events
    Queue(
        f"{EXCHANGE_NAME}.tenant_group_assignment",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant_group_assignment.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant_group_assignment.dlq",
        },
    ),
    # Tenant integration events
    Queue(
        f"{EXCHANGE_NAME}.tenant_integration",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.tenant_integration.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.tenant_integration.dlq",
        },
    ),
    # User account events (global)
    Queue(
        f"{EXCHANGE_NAME}.user_account",
        exchange=tenant_mngr_srv_exchange,
        routing_key=f"{EXCHANGE_NAME}.user_account.#",
        queue_arguments={
            "x-dead-letter-exchange": tenant_mngr_srv_dlx.name,
            "x-dead-letter-routing-key": f"{EXCHANGE_NAME}.user_account.dlq",
        },
    ),
)

# Append dead-letter queues for the new domain objects
celery_app.conf.task_queues += (
    Queue(
        f"{EXCHANGE_NAME}.tenant_user.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant_user.dlq",
    ),
    Queue(
        f"{EXCHANGE_NAME}.tenant_role.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant_role.dlq",
    ),
    Queue(
        f"{EXCHANGE_NAME}.tenant_group.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant_group.dlq",
    ),
    Queue(
        f"{EXCHANGE_NAME}.tenant_role_assignment.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant_role_assignment.dlq",
    ),
    Queue(
        f"{EXCHANGE_NAME}.tenant_group_assignment.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant_group_assignment.dlq",
    ),
    Queue(
        f"{EXCHANGE_NAME}.tenant_integration.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.tenant_integration.dlq",
    ),
    Queue(
        f"{EXCHANGE_NAME}.user_account.dlq",
        exchange=tenant_mngr_srv_dlx,
        routing_key=f"{EXCHANGE_NAME}.user_account.dlq",
    ),
)

# Routing rules map task names to queues and routing keys.  All task names
# must be prefixed with ``tenant_mngr_srv.`` to ensure they go through the single
# exchange defined above.
celery_app.conf.task_routes = {
    # Tenant events
    f"{EXCHANGE_NAME}.tenant.created": {
        "queue": f"{EXCHANGE_NAME}.tenant",
        "routing_key": f"{EXCHANGE_NAME}.tenant.created",
    },
    f"{EXCHANGE_NAME}.tenant.updated": {
        "queue": f"{EXCHANGE_NAME}.tenant",
        "routing_key": f"{EXCHANGE_NAME}.tenant.updated",
    },
    f"{EXCHANGE_NAME}.tenant.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant",
        "routing_key": f"{EXCHANGE_NAME}.tenant.deleted",
    },
    # Tenant user events
    f"{EXCHANGE_NAME}.tenant_user.created": {
        "queue": f"{EXCHANGE_NAME}.tenant_user",
        "routing_key": f"{EXCHANGE_NAME}.tenant_user.created",
    },
    f"{EXCHANGE_NAME}.tenant_user.updated": {
        "queue": f"{EXCHANGE_NAME}.tenant_user",
        "routing_key": f"{EXCHANGE_NAME}.tenant_user.updated",
    },
    f"{EXCHANGE_NAME}.tenant_user.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant_user",
        "routing_key": f"{EXCHANGE_NAME}.tenant_user.deleted",
    },
    # Tenant role events
    f"{EXCHANGE_NAME}.tenant_role.created": {
        "queue": f"{EXCHANGE_NAME}.tenant_role",
        "routing_key": f"{EXCHANGE_NAME}.tenant_role.created",
    },
    f"{EXCHANGE_NAME}.tenant_role.updated": {
        "queue": f"{EXCHANGE_NAME}.tenant_role",
        "routing_key": f"{EXCHANGE_NAME}.tenant_role.updated",
    },
    f"{EXCHANGE_NAME}.tenant_role.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant_role",
        "routing_key": f"{EXCHANGE_NAME}.tenant_role.deleted",
    },
    # Tenant group events
    f"{EXCHANGE_NAME}.tenant_group.created": {
        "queue": f"{EXCHANGE_NAME}.tenant_group",
        "routing_key": f"{EXCHANGE_NAME}.tenant_group.created",
    },
    f"{EXCHANGE_NAME}.tenant_group.updated": {
        "queue": f"{EXCHANGE_NAME}.tenant_group",
        "routing_key": f"{EXCHANGE_NAME}.tenant_group.updated",
    },
    f"{EXCHANGE_NAME}.tenant_group.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant_group",
        "routing_key": f"{EXCHANGE_NAME}.tenant_group.deleted",
    },
    # Tenant role assignment events
    f"{EXCHANGE_NAME}.tenant_role_assignment.created": {
        "queue": f"{EXCHANGE_NAME}.tenant_role_assignment",
        "routing_key": f"{EXCHANGE_NAME}.tenant_role_assignment.created",
    },
    f"{EXCHANGE_NAME}.tenant_role_assignment.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant_role_assignment",
        "routing_key": f"{EXCHANGE_NAME}.tenant_role_assignment.deleted",
    },
    # Tenant group assignment events
    f"{EXCHANGE_NAME}.tenant_group_assignment.created": {
        "queue": f"{EXCHANGE_NAME}.tenant_group_assignment",
        "routing_key": f"{EXCHANGE_NAME}.tenant_group_assignment.created",
    },
    f"{EXCHANGE_NAME}.tenant_group_assignment.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant_group_assignment",
        "routing_key": f"{EXCHANGE_NAME}.tenant_group_assignment.deleted",
    },
    # Tenant integration events
    f"{EXCHANGE_NAME}.tenant_integration.created": {
        "queue": f"{EXCHANGE_NAME}.tenant_integration",
        "routing_key": f"{EXCHANGE_NAME}.tenant_integration.created",
    },
    f"{EXCHANGE_NAME}.tenant_integration.updated": {
        "queue": f"{EXCHANGE_NAME}.tenant_integration",
        "routing_key": f"{EXCHANGE_NAME}.tenant_integration.updated",
    },
    f"{EXCHANGE_NAME}.tenant_integration.deleted": {
        "queue": f"{EXCHANGE_NAME}.tenant_integration",
        "routing_key": f"{EXCHANGE_NAME}.tenant_integration.deleted",
    },
    # User account events
    f"{EXCHANGE_NAME}.user_account.created": {
        "queue": f"{EXCHANGE_NAME}.user_account",
        "routing_key": f"{EXCHANGE_NAME}.user_account.created",
    },
    f"{EXCHANGE_NAME}.user_account.updated": {
        "queue": f"{EXCHANGE_NAME}.user_account",
        "routing_key": f"{EXCHANGE_NAME}.user_account.updated",
    },
    f"{EXCHANGE_NAME}.user_account.deleted": {
        "queue": f"{EXCHANGE_NAME}.user_account",
        "routing_key": f"{EXCHANGE_NAME}.user_account.deleted",
    },
}

# --------------------------------------------------------------------
# Task discovery (for the *consumer* side)
# --------------------------------------------------------------------
celery_app.autodiscover_tasks(
    [
        "app.workers.tasks",
    ]
)

# Initialise telemetry for Celery workers when they start up.
try:
    init_tracing(service_name=f"{EXCHANGE_NAME}.worker")
    instrument_celery(celery_app)
    # Instrument httpx globally for Celery worker processes
    from app.core.telemetry import instrument_httpx
    instrument_httpx()
except Exception:
    # Telemetry may not be available; ignore
    pass
