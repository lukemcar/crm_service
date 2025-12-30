"""Tests for the CRM message producers.

These tests verify that the contact and company producers build
messages using the correct task names, headers and payloads.  The
``BaseProducer._send`` method is patched to avoid sending to an
actual broker and to capture the arguments passed.  Only a subset of
message types are tested here; full coverage can be achieved by
repeating the pattern for update and delete events if desired.
"""

from __future__ import annotations

from uuid import uuid4
from unittest.mock import patch

import pytest

from app.core.celery_app import EXCHANGE_NAME
from app.messaging.producers.contact_producer import ContactMessageProducer
from app.messaging.producers.company_producer import CompanyMessageProducer


def test_contact_producer_created() -> None:
    """Verify that ContactMessageProducer publishes a contact.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "first_name": "Test"}
    with patch.object(ContactMessageProducer, "_send") as mocked_send:
        ContactMessageProducer.send_contact_created(tenant_id=tenant_id, payload=payload)
        # Ensure _send was invoked once
        assert mocked_send.call_count == 1
        # Examine the keyword arguments passed to _send
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.contact.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_company_producer_created() -> None:
    """Verify that CompanyMessageProducer publishes a company.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "name": "ACME"}
    with patch.object(CompanyMessageProducer, "_send") as mocked_send:
        CompanyMessageProducer.send_company_created(tenant_id=tenant_id, payload=payload)
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.company.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)
