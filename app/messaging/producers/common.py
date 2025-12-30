


from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4
from datetime import datetime

# import the shared Celery app and exchange name once
from app.core.celery_app import celery_app, EXCHANGE_NAME
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import (
    get_correlation_id,
    get_message_id,
    set_message_id,
)


class BaseProducer:

    @classmethod
    def _send(
        cls,
        *,
        task_name: str,
        message_model: Any,
        headers: Dict[str, str],
    ) -> None:
        """
        Internal helper: wrap the domain message in an EventEnvelope and
        send it via Celery.  Adds correlation and causation identifiers
        to enable tracing across services.
        """
        payload = message_model.model_dump(mode="json")
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type=task_name,
            schema_version=1,
            occurred_at=datetime.utcnow(),
            producer=EXCHANGE_NAME,
            tenant_id=message_model.tenant_id,
            correlation_id=get_correlation_id(),
            causation_id=get_message_id(),
            traceparent=None,
            data=payload,
        )
        # update context so downstream producers use this event_id as causation
        set_message_id(str(envelope.event_id))
        correlation_headers = {
            "message_id": str(envelope.event_id),
            "correlation_id": str(envelope.correlation_id)
            if envelope.correlation_id is not None
            else None,
            "causation_id": str(envelope.causation_id)
            if envelope.causation_id is not None
            else None,
        }
        correlation_headers = {k: v for k, v in correlation_headers.items() if v}
        combined_headers = {**headers, **correlation_headers}
        celery_app.send_task(
            name=task_name,
            kwargs={"envelope": envelope.model_dump(mode="json")},
            headers=combined_headers,
        )