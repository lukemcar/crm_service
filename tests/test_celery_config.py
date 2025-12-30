"""Tests for the Celery configuration.

These tests ensure that the CRM Celery application is configured with
the expected exchange name and routing rules.  They do not start
workers or interact with a broker; instead, they assert on the
configuration dictionary exposed via the Celery app.  If the routing
table changes, update these assertions accordingly.
"""

from __future__ import annotations

from app.core.celery_app import celery_app, EXCHANGE_NAME


def test_celery_exchange_name() -> None:
    """The Celery exchange name should be "crm"."""
    assert EXCHANGE_NAME == "crm"


def test_celery_task_routing() -> None:
    """Verify that contact.created and company.updated tasks are routed correctly."""
    routes = celery_app.conf.task_routes
    # Contact created events should route to the contact queue with a matching routing key
    assert routes[f"{EXCHANGE_NAME}.contact.created"]["queue"] == f"{EXCHANGE_NAME}.contact"
    assert routes[f"{EXCHANGE_NAME}.contact.created"]["routing_key"] == f"{EXCHANGE_NAME}.contact.created"
    # Company updated events should route to the company queue
    assert routes[f"{EXCHANGE_NAME}.company.updated"]["queue"] == f"{EXCHANGE_NAME}.company"
    assert routes[f"{EXCHANGE_NAME}.company.updated"]["routing_key"] == f"{EXCHANGE_NAME}.company.updated"
