"""
Service layer for AutomationActionExecution entities.

This module provides operations to record and update execution logs for
automation actions.  Executions are primarily created by the automation
engine rather than external clients, so creation functions expect the
tenant and action context to be supplied by the caller.  Status updates
should reflect transitions through the execution lifecycle (PENDING,
IN_PROGRESS, SUCCEEDED, FAILED).  Consumers can query execution records
by action, status or entity context for monitoring and debugging.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.automation_action_execution import AutomationActionExecution
from app.domain.schemas.automation_action_execution import (
    AutomationActionExecutionCreate,
    AutomationActionExecutionRead,
)
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.automation_action_execution_producer import (
    AutomationActionExecutionMessageProducer,
)

logger = logging.getLogger("automation_action_execution_service")


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Convert an ISO timestamp string to a datetime object, if provided."""
    if ts is None:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid datetime format: {ts}",
        )


def create_execution(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
    request: AutomationActionExecutionCreate,
) -> AutomationActionExecution:
    """Create a new automation action execution record.

    The execution is initialized with status ``PENDING``.  The ``execution_key`` must
    be unique per tenant; violations will surface as integrity errors via
    commit_or_raise.
    """
    logger.debug(
        "Creating execution: tenant_id=%s, action_id=%s, execution_key=%s",
        tenant_id,
        action_id,
        request.execution_key,
    )
    entry = AutomationActionExecution(
        tenant_id=tenant_id,
        action_id=action_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        pipeline_id=request.pipeline_id,
        from_stage_id=request.from_stage_id,
        to_stage_id=request.to_stage_id,
        list_id=request.list_id,
        trigger_event=request.trigger_event,
        execution_key=request.execution_key,
        status="PENDING",
        response_code=request.response_code,
        response_body=request.response_body,
        error_message=request.error_message,
        triggered_at=_parse_iso(request.triggered_at) if request.triggered_at else datetime.utcnow(),
        started_at=_parse_iso(request.started_at) if request.started_at else None,
        completed_at=_parse_iso(request.completed_at) if request.completed_at else None,
    )
    db.add(entry)
    commit_or_raise(db, refresh=entry, action="create automation action execution")
    return entry


def get_execution(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    execution_id: uuid.UUID,
) -> AutomationActionExecution:
    """Retrieve an execution record by ID within a tenant context."""
    entry = (
        db.query(AutomationActionExecution)
        .filter(
            AutomationActionExecution.id == execution_id,
            AutomationActionExecution.tenant_id == tenant_id,
        )
        .first()
    )
    if not entry:
        logger.info(
            "Execution record not found: tenant_id=%s, id=%s", tenant_id, execution_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution record not found")
    return entry


def _execution_snapshot(entry: AutomationActionExecution) -> Dict[str, Any]:
    """Return a dictionary representation of an AutomationActionExecution for event payloads."""
    read_model = AutomationActionExecutionRead.model_validate(entry, from_attributes=True)
    return read_model.model_dump()


def update_execution_status(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    execution_id: uuid.UUID,
    status: str,
    response_code: Optional[int] = None,
    response_body: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> AutomationActionExecution:
    """Update the status and optional fields of an execution record.

    Status transitions are not strictly validated here; callers should enforce
    appropriate state progression.  Timestamps can be provided as ISO strings
    and will be parsed to datetime objects.  Messaging events, if required,
    should be emitted by the caller after this update succeeds.
    """
    entry = get_execution(db, tenant_id=tenant_id, execution_id=execution_id)
    entry.status = status
    if response_code is not None:
        entry.response_code = response_code
    if response_body is not None:
        entry.response_body = response_body
    if error_message is not None:
        entry.error_message = error_message
    if started_at is not None:
        entry.started_at = _parse_iso(started_at)
    if completed_at is not None:
        entry.completed_at = _parse_iso(completed_at)
    commit_or_raise(db, refresh=entry, action="update automation action execution")
    # Emit status changed event after successful commit
    try:
        payload = _execution_snapshot(entry)
        AutomationActionExecutionMessageProducer.send_execution_status_changed(
            tenant_id=tenant_id,
            execution_id=entry.id,
            action_id=entry.action_id,
            status=entry.status,
            payload=payload,
            changed_dt=datetime.utcnow().isoformat(),
        )
    except Exception:
        # Suppress messaging errors; classification handled by messaging layer
        pass
    return entry


def list_executions_by_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[AutomationActionExecution], int]:
    """List execution records for a given action and optional status filter."""
    query = db.query(AutomationActionExecution).filter(
        AutomationActionExecution.tenant_id == tenant_id,
        AutomationActionExecution.action_id == action_id,
    )
    if status:
        query = query.filter(AutomationActionExecution.status == status)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(AutomationActionExecution.created_at.desc())
    return query.all(), total


def list_executions_by_entity(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[AutomationActionExecution], int]:
    """List execution records for a given entity and optional status filter."""
    query = db.query(AutomationActionExecution).filter(
        AutomationActionExecution.tenant_id == tenant_id,
        AutomationActionExecution.entity_type == entity_type,
        AutomationActionExecution.entity_id == entity_id,
    )
    if status:
        query = query.filter(AutomationActionExecution.status == status)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(AutomationActionExecution.created_at.desc())
    return query.all(), total


__all__ = [
    "create_execution",
    "get_execution",
    "update_execution_status",
    "list_executions_by_action",
    "list_executions_by_entity",
]