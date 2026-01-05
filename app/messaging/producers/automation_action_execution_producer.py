"""
Producer for automation action execution status change events.

This module encapsulates the publishing logic for automation action execution
status events.  When an execution record changes status (e.g. from PENDING to
IN_PROGRESS or to SUCCEEDED/FAILED), an event is emitted to notify
subscribers.  The task name follows the ``<exchange>.automation_action_execution.status_changed``
convention consistent with other domain producers.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import EXCHANGE_NAME
from app.domain.schemas.events.automation_action_execution_event import (
    AutomationActionExecutionStatusChangedEvent,
)
from .common import BaseProducer


class AutomationActionExecutionMessageProducer(BaseProducer):
    """Publishes automation action execution status events via Celery."""

    TASK_STATUS_CHANGED: str = (
        f"{EXCHANGE_NAME}.automation_action_execution.status_changed"
    )

    @staticmethod
    def _build_headers(
        *, tenant_id: UUID, action_id: UUID, execution_id: UUID
    ) -> Dict[str, str]:
        """Construct message headers for routing and correlation."""
        return {
            "tenant_id": str(tenant_id),
            "action_id": str(action_id),
            "execution_id": str(execution_id),
        }

    @classmethod
    def send_execution_status_changed(
        cls,
        *,
        tenant_id: UUID,
        execution_id: UUID,
        action_id: UUID,
        status: str,
        payload: Dict[str, Any],
        changed_dt: str | None = None,
    ) -> None:
        """Publish an automation_action_execution.status_changed event.

        Parameters
        ----------
        tenant_id : UUID
            Identifier of the tenant that owns the execution.
        execution_id : UUID
            Identifier of the execution record.
        action_id : UUID
            Identifier of the automation action.
        status : str
            The new status of the execution.
        payload : dict
            A full snapshot of the execution record after the status change.
        changed_dt : str | None, optional
            ISO timestamp indicating when the status change occurred.
        """
        message = AutomationActionExecutionStatusChangedEvent(
            tenant_id=tenant_id,
            execution_id=execution_id,
            action_id=action_id,
            status=status,
            payload=payload,
            changed_dt=changed_dt,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id, action_id=action_id, execution_id=execution_id
        )
        cls._send(
            task_name=cls.TASK_STATUS_CHANGED,
            message_model=message,
            headers=headers,
        )


__all__ = ["AutomationActionExecutionMessageProducer"]