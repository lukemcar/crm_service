"""
Service layer for automation actions.

This module provides functions to create, list, update and delete
automation actions.  Validation occurs at the service level to ensure
exactly one scope target is set and tenant identifiers match.  After
committing database transactions, events are published via the
messaging layer.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, Tuple, List as TypingList

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.automation_action import AutomationAction
from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionUpdate,
    AutomationActionRead,
)
from app.domain.services.common_service import commit_or_raise
from app.messaging.producers.automation_action_producer import AutomationActionMessageProducer


def _action_snapshot(action: AutomationAction) -> Dict[str, Any]:
    """Create a snapshot dictionary of an automation action for event payloads."""
    read_model = AutomationActionRead.model_validate(action, from_attributes=True)
    return read_model.model_dump()


def _validate_scope(action_in: AutomationActionCreate | AutomationActionUpdate) -> None:
    """Ensure that exactly one scope target is provided.

    Raises HTTPException if the validation fails.
    """
    # Count how many target identifiers are non‑null
    targets = [
        getattr(action_in, "record_id", None),
        getattr(action_in, "pipeline_id", None),
        getattr(action_in, "pipeline_stage_id", None),
        getattr(action_in, "list_id", None),
    ]
    count = sum(1 for t in targets if t is not None)
    if count != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one of record_id, pipeline_id, pipeline_stage_id, list_id must be provided",
        )


def service_list_actions(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    entity_type: Optional[str] = None,
    scope_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[TypingList[AutomationAction], int]:
    """List automation actions filtered by tenant and optional criteria."""
    query = db.query(AutomationAction).filter(AutomationAction.tenant_id == tenant_id)
    if entity_type is not None:
        query = query.filter(AutomationAction.entity_type == entity_type)
    if scope_type is not None:
        query = query.filter(AutomationAction.scope_type == scope_type)
    if enabled is not None:
        query = query.filter(AutomationAction.enabled == enabled)
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all(), total


def service_create_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_in: AutomationActionCreate,
    created_by_user_id: Optional[uuid.UUID] = None,
) -> AutomationAction:
    """Create a new automation action and emit a created event.

    Raises 400 if the tenant_id does not match or if scope validation fails.
    """
    if action_in.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID mismatch")
    # Validate exactly one scope target is provided
    _validate_scope(action_in)
    action = AutomationAction(
        tenant_id=tenant_id,
        entity_type=action_in.entity_type,
        scope_type=action_in.scope_type,
        record_type=action_in.record_type,
        record_id=action_in.record_id,
        pipeline_id=action_in.pipeline_id,
        pipeline_stage_id=action_in.pipeline_stage_id,
        list_id=action_in.list_id,
        trigger_event=action_in.trigger_event,
        condition_json=action_in.condition_json,
        action_type=action_in.action_type,
        config_json=action_in.config_json,
        priority=action_in.priority or 0,
        enabled=action_in.enabled if action_in.enabled is not None else True,
        inherit_pipeline_actions=action_in.inherit_pipeline_actions if action_in.inherit_pipeline_actions is not None else True,
    )
    db.add(action)
    commit_or_raise(db, refresh=action)
    # Publish created event
    try:
        payload = _action_snapshot(action)
        AutomationActionMessageProducer.send_action_created(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        pass
    return action


def service_update_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
    update_in: AutomationActionUpdate,
    updated_by_user_id: Optional[uuid.UUID] = None,
) -> AutomationAction:
    """Update an existing automation action and emit an updated event."""
    action = (
        db.query(AutomationAction)
        .filter(AutomationAction.tenant_id == tenant_id, AutomationAction.id == action_id)
        .first()
    )
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation action not found")
    # Apply updates to fields if provided
    for field, value in update_in:
        if value is not None:
            setattr(action, field, value)
    # Validate scope if any scope field was updated
    if any(
        getattr(update_in, name) is not None
        for name in ["record_id", "pipeline_id", "pipeline_stage_id", "list_id"]
    ):
        # Compose a temporary model to validate scope counts
        temp = AutomationActionCreate(
            tenant_id=tenant_id,
            entity_type=action.entity_type,
            scope_type=action.scope_type,
            record_type=action.record_type,
            record_id=action.record_id,
            pipeline_id=action.pipeline_id,
            pipeline_stage_id=action.pipeline_stage_id,
            list_id=action.list_id,
            trigger_event=action.trigger_event,
            condition_json=action.condition_json,
            action_type=action.action_type,
            config_json=action.config_json,
            priority=action.priority,
            enabled=action.enabled,
            inherit_pipeline_actions=action.inherit_pipeline_actions,
        )
        _validate_scope(temp)
    commit_or_raise(db, refresh=action)
    # Publish updated event
    try:
        payload = _action_snapshot(action)
        AutomationActionMessageProducer.send_action_updated(
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        pass
    return action


def service_delete_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
    deleted_by_user_id: Optional[uuid.UUID] = None,
) -> None:
    """Delete an automation action and emit a deleted event."""
    action = (
        db.query(AutomationAction)
        .filter(AutomationAction.tenant_id == tenant_id, AutomationAction.id == action_id)
        .first()
    )
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation action not found")
    db.delete(action)
    commit_or_raise(db)
    # Publish deleted event
    try:
        AutomationActionMessageProducer.send_action_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        pass
