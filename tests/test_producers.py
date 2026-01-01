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
from app.messaging.producers.group_profile_producer import GroupProfileMessageProducer
from app.messaging.producers.inbound_channel_producer import InboundChannelMessageProducer
from app.messaging.producers.ticket_producer import TicketMessageProducer
from app.messaging.producers.ticket_participant_producer import TicketParticipantMessageProducer
from app.messaging.producers.ticket_tag_producer import TicketTagMessageProducer
from app.messaging.producers.ticket_message_producer import TicketMessageMessageProducer
from app.messaging.producers.ticket_attachment_producer import TicketAttachmentMessageProducer
from app.messaging.producers.ticket_assignment_producer import TicketAssignmentMessageProducer
from app.messaging.producers.ticket_audit_producer import TicketAuditMessageProducer
from app.messaging.producers.ticket_form_producer import TicketFormMessageProducer
from app.messaging.producers.ticket_form_field_producer import TicketFormFieldMessageProducer
from app.messaging.producers.ticket_field_value_producer import TicketFieldValueMessageProducer
from app.messaging.producers.support_view_producer import SupportViewMessageProducer
from app.messaging.producers.support_macro_producer import SupportMacroMessageProducer
from app.messaging.producers.ticket_task_mirror_producer import TicketTaskMirrorMessageProducer
from app.messaging.producers.ticket_ai_work_ref_producer import TicketAiWorkRefMessageProducer
from app.messaging.producers.ticket_metrics_producer import TicketMetricsMessageProducer
from app.messaging.producers.ticket_status_duration_producer import TicketStatusDurationMessageProducer
from app.messaging.producers.kb_category_producer import KbCategoryMessageProducer



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


def test_group_profile_producer_created() -> None:
    """Verify that GroupProfileMessageProducer publishes a group_profile.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "group_id": "grp"}
    with patch.object(GroupProfileMessageProducer, "_send") as mocked_send:
        GroupProfileMessageProducer.send_group_profile_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.group_profile.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_inbound_channel_producer_created() -> None:
    """Verify that InboundChannelMessageProducer publishes an inbound_channel.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "channel_type": "email"}
    with patch.object(InboundChannelMessageProducer, "_send") as mocked_send:
        InboundChannelMessageProducer.send_inbound_channel_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.inbound_channel.created"
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


def test_ticket_producer_created() -> None:
    """Verify that TicketMessageProducer publishes a ticket.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "subject": "Test"}
    with patch.object(TicketMessageProducer, "_send") as mocked_send:
        TicketMessageProducer.send_ticket_created(tenant_id=tenant_id, payload=payload)
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_participant_producer_created() -> None:
    """Verify that TicketParticipantMessageProducer publishes a ticket_participant.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_id": "tid", "participant_type": "agent"}
    with patch.object(TicketParticipantMessageProducer, "_send") as mocked_send:
        TicketParticipantMessageProducer.send_ticket_participant_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_participant.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_tag_producer_created() -> None:
    """Verify that TicketTagMessageProducer publishes a ticket_tag.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_id": "tid", "tag": "urgent"}
    with patch.object(TicketTagMessageProducer, "_send") as mocked_send:
        TicketTagMessageProducer.send_ticket_tag_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_tag.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_message_producer_created() -> None:
    """Verify that TicketMessageMessageProducer publishes a ticket_message.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_id": "tid", "body": "Hello"}
    with patch.object(TicketMessageMessageProducer, "_send") as mocked_send:
        TicketMessageMessageProducer.send_ticket_message_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_message.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_attachment_producer_created() -> None:
    """Verify that TicketAttachmentMessageProducer publishes a ticket_attachment.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_id": "tid", "file_name": "doc.pdf"}
    with patch.object(TicketAttachmentMessageProducer, "_send") as mocked_send:
        TicketAttachmentMessageProducer.send_ticket_attachment_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_attachment.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_assignment_producer_created() -> None:
    """Verify that TicketAssignmentMessageProducer publishes a ticket_assignment.created event."""
    tenant_id = uuid4()
    payload = {
        "id": "dummy",
        "ticket_id": "tid",
        "assigned_group_id": "grp",
    }
    with patch.object(TicketAssignmentMessageProducer, "_send") as mocked_send:
        TicketAssignmentMessageProducer.send_ticket_assignment_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_assignment.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_audit_producer_created() -> None:
    """Verify that TicketAuditMessageProducer publishes a ticket_audit.created event."""
    tenant_id = uuid4()
    payload = {
        "id": "dummy",
        "ticket_id": "tid",
        "event_type": "status_changed",
    }
    with patch.object(TicketAuditMessageProducer, "_send") as mocked_send:
        TicketAuditMessageProducer.send_ticket_audit_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_audit.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_form_producer_created() -> None:
    """Verify that TicketFormMessageProducer publishes a ticket_form.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "name": "Custom Form"}
    with patch.object(TicketFormMessageProducer, "_send") as mocked_send:
        TicketFormMessageProducer.send_ticket_form_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_form.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_form_field_producer_created() -> None:
    """Verify that TicketFormFieldMessageProducer publishes a ticket_form_field.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_form_id": "fid", "ticket_field_def_id": "def", "display_order": 0}
    with patch.object(TicketFormFieldMessageProducer, "_send") as mocked_send:
        TicketFormFieldMessageProducer.send_ticket_form_field_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_form_field.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_field_value_producer_created() -> None:
    """Verify that TicketFieldValueMessageProducer publishes a ticket_field_value.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_id": "tid", "ticket_field_def_id": "def", "value_text": "val"}
    with patch.object(TicketFieldValueMessageProducer, "_send") as mocked_send:
        TicketFieldValueMessageProducer.send_ticket_field_value_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_field_value.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_support_view_producer_created() -> None:
    """Verify that SupportViewMessageProducer publishes a support_view.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "name": "View"}
    with patch.object(SupportViewMessageProducer, "_send") as mocked_send:
        SupportViewMessageProducer.send_support_view_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.support_view.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_support_macro_producer_created() -> None:
    """Verify that SupportMacroMessageProducer publishes a support_macro.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "name": "Macro"}
    with patch.object(SupportMacroMessageProducer, "_send") as mocked_send:
        SupportMacroMessageProducer.send_support_macro_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.support_macro.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_task_mirror_producer_created() -> None:
    """Verify that TicketTaskMirrorMessageProducer publishes a ticket_task_mirror.created event."""
    tenant_id = uuid4()
    payload = {
        "id": "dummy",
        "ticket_id": "tid",
        "orchestration_task_id": "task",
        "name": "Task",
    }
    with patch.object(TicketTaskMirrorMessageProducer, "_send") as mocked_send:
        TicketTaskMirrorMessageProducer.send_ticket_task_mirror_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_task_mirror.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_ai_work_ref_producer_created() -> None:
    """Verify that TicketAiWorkRefMessageProducer publishes a ticket_ai_work_ref.created event."""
    tenant_id = uuid4()
    payload = {
        "id": "dummy",
        "ticket_id": "tid",
        "ai_session_id": str(uuid4()),
        "agent_key": "agent",
        "purpose": "triage",
    }
    with patch.object(TicketAiWorkRefMessageProducer, "_send") as mocked_send:
        TicketAiWorkRefMessageProducer.send_ticket_ai_work_ref_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_ai_work_ref.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_metrics_producer_created() -> None:
    """Verify that TicketMetricsMessageProducer publishes a ticket_metrics.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "ticket_id": "tid", "reply_count": 2, "reopen_count": 1}
    with patch.object(TicketMetricsMessageProducer, "_send") as mocked_send:
        TicketMetricsMessageProducer.send_ticket_metrics_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_metrics.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_ticket_status_duration_producer_created() -> None:
    """Verify that TicketStatusDurationMessageProducer publishes a ticket_status_duration.created event."""
    tenant_id = uuid4()
    payload = {
        "id": "dummy",
        "ticket_id": "tid",
        "status": "open",
        "started_at": "2024-01-01T00:00:00",
        "ended_at": None,
        "duration_seconds": None,
    }
    with patch.object(TicketStatusDurationMessageProducer, "_send") as mocked_send:
        TicketStatusDurationMessageProducer.send_ticket_status_duration_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.ticket_status_duration.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)


def test_kb_category_producer_created() -> None:
    """Verify that KbCategoryMessageProducer publishes a kb_category.created event."""
    tenant_id = uuid4()
    payload = {"id": "dummy", "name": "Category"}
    with patch.object(KbCategoryMessageProducer, "_send") as mocked_send:
        KbCategoryMessageProducer.send_kb_category_created(
            tenant_id=tenant_id, payload=payload
        )
        assert mocked_send.call_count == 1
        _, kwargs = mocked_send.call_args
        assert kwargs["task_name"] == f"{EXCHANGE_NAME}.kb_category.created"
        message = kwargs["message_model"]
        assert message.tenant_id == tenant_id
        assert message.payload == payload
        headers = kwargs["headers"]
        assert headers["tenant_id"] == str(tenant_id)
