"""
Service layer for automation action execution records.

This module provides functions to create, update and list automation
action executions.  Validation occurs at the service level to ensure
tenant identifiers match, execution keys are unique per tenant and
status transitions are valid.  The service leverages
``commit_or_raise`` to handle database commits and translate common
database errors into HTTP exceptions.
"""

from __future__ import annotations

import uuid
from typing import List as TypingList, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.automation_action_execution import AutomationActionExecution
from app.domain.schemas.automation_action_execution import (
    AutomationActionExecutionCreate,
    AutomationActionExecutionUpdate,
    AutomationActionExecutionRead,
)
from app.domain.services.common_service import commit_or_raise


# Allowed execution status values
ALLOWED_STATUSES: set[str] = {"PENDING", "IN_PROGRESS", "SUCCEEDED", "FAILED"}


def _execution_snapshot(exe: AutomationActionExecution) -> dict:
    """Create a snapshot dictionary of an execution for API responses."""
    read_model = AutomationActionExecutionRead.model_validate(exe, from_attributes=True)
    return read_model.model_dump()


def service_create_execution(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    execution_in: AutomationActionExecutionCreate,
) -> AutomationActionExecution:
    """Create a new automation action execution.

    Raises 400 if the tenant_id does not match, or 409 on unique constraint violation.
    """
    # Ensure tenant_id matches input
    if execution_in.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID mismatch")
    # Ensure status is valid; default is PENDING
    status_val = execution_in.status or "PENDING"
    if status_val not in ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid execution status")
    # Build model instance
    exe = AutomationActionExecution(
        tenant_id=tenant_id,
        action_id=execution_in.action_id,
        entity_type=execution_in.entity_type,
        entity_id=execution_in.entity_id,
        pipeline_id=execution_in.pipeline_id,
        from_stage_id=execution_in.from_stage_id,
        to_stage_id=execution_in.to_stage_id,
        list_id=execution_in.list_id,
        trigger_event=execution_in.trigger_event,
        execution_key=execution_in.execution_key,
        status=status_val,
        response_code=execution_in.response_code,
        response_body=execution_in.response_body,
        error_message=execution_in.error_message,
        triggered_at=execution_in.triggered_at or None,
        started_at=execution_in.started_at,
        completed_at=execution_in.completed_at,
    )
    db.add(exe)
    commit_or_raise(db, refresh=exe)
    return exe


def service_update_execution(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    execution_id: uuid.UUID,
    update_in: AutomationActionExecutionUpdate,
) -> AutomationActionExecution:
    """Update an existing execution's status or response fields.

    Raises 404 if the execution is not found or does not belong to the tenant.
    Raises 400 if an invalid status is provided.
    """
    exe = (
        db.query(AutomationActionExecution)
        .filter(
            AutomationActionExecution.tenant_id == tenant_id,
            AutomationActionExecution.id == execution_id,
        )
        .first()
    )
    if not exe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    # Validate new status
    if update_in.status is not None and update_in.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid execution status")
    # Apply updates
    for field, value in update_in:
        if value is not None:
            setattr(exe, field, value)
    commit_or_raise(db, refresh=exe)
    return exe


def service_list_executions(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[AutomationActionExecution], int]:
    """List executions filtered by tenant and optional criteria."""
    query = db.query(AutomationActionExecution).filter(AutomationActionExecution.tenant_id == tenant_id)
    if action_id is not None:
        query = query.filter(AutomationActionExecution.action_id == action_id)
    if entity_type is not None:
        query = query.filter(AutomationActionExecution.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(AutomationActionExecution.entity_id == entity_id)
    if status_filter is not None:
        query = query.filter(AutomationActionExecution.status == status_filter)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_get_execution(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    execution_id: uuid.UUID,
) -> AutomationActionExecution:
    """Retrieve a single execution by its ID and tenant."""
    exe = (
        db.query(AutomationActionExecution)
        .filter(
            AutomationActionExecution.tenant_id == tenant_id,
            AutomationActionExecution.id == execution_id,
        )
        .first()
    )
    if not exe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return exe
