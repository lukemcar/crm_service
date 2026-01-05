"""
Service layer for AutomationAction entities.

This module provides CRUD operations for automation actions, ensuring
tenant scoping, enforcing scope constraints at the application layer and
emitting domain events upon successful mutations.  Listing operations
support optional filtering by entity_type and scope_type and support
pagination.  Unique and check constraints are enforced at the database
layer; violations will surface as integrity errors via commit_or_raise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.automation_action import AutomationAction
from app.domain.schemas.automation_action import (
    AutomationActionCreate,
    AutomationActionUpdate,
    AutomationActionRead,
)
from app.domain.schemas.events.automation_action_event import (
    AutomationActionDelta,
)
from app.messaging.producers.automation_action_producer import (
    AutomationActionMessageProducer as AutomationActionProducer,
)
from app.domain.services.common_service import commit_or_raise

logger = logging.getLogger("automation_action_service")


def _snapshot(action: AutomationAction) -> Dict[str, Any]:
    """Return a dictionary representation of an AutomationAction for event payloads."""
    read_model = AutomationActionRead.model_validate(action, from_attributes=True)
    return read_model.model_dump()


def _compute_delta(action: AutomationAction, updates: Dict[str, Any]) -> AutomationActionDelta:
    """Compute a delta object for modified base fields on an automation action."""
    changed: Dict[str, Any] = {}
    for field, value in updates.items():
        if value is None:
            continue
        current = getattr(action, field)
        # Compare values; for datetimes convert to ISO strings for equality
        if isinstance(current, datetime):
            current_val = current.isoformat()
        else:
            current_val = current
        new_val = value.isoformat() if isinstance(value, datetime) else value
        if current_val != new_val:
            changed[field] = value
    return AutomationActionDelta(base_fields=changed or None)


def list_automation_actions(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    scope_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[AutomationAction], int]:
    """List automation actions with optional filtering by entity_type and scope_type.

    If ``tenant_id`` is provided, results are scoped to that tenant.  Filters
    perform exact matches on ``entity_type`` and ``scope_type``.  Results are
    ordered by creation time descending and can be paginated via ``limit`` and
    ``offset``.  Returns the list of actions and the total count.
    """
    logger.debug(
        "Listing automation actions: tenant_id=%s, entity_type=%s, scope_type=%s, limit=%s, offset=%s",
        tenant_id,
        entity_type,
        scope_type,
        limit,
        offset,
    )
    query = db.query(AutomationAction)
    if tenant_id is not None:
        query = query.filter(AutomationAction.tenant_id == tenant_id)
    if entity_type:
        query = query.filter(AutomationAction.entity_type == entity_type)
    if scope_type:
        query = query.filter(AutomationAction.scope_type == scope_type)
    total = query.count()
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    query = query.order_by(AutomationAction.created_at.desc())
    return query.all(), total


def create_automation_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: AutomationActionCreate,
    created_by: str,
) -> AutomationAction:
    """Create a new automation action and publish a created event."""
    logger.debug(
        "Creating automation action: tenant_id=%s, entity_type=%s, scope_type=%s, trigger_event=%s",
        tenant_id,
        request.entity_type,
        request.scope_type,
        request.trigger_event,
    )
    action = AutomationAction(
        tenant_id=tenant_id,
        entity_type=request.entity_type,
        scope_type=request.scope_type,
        record_type=request.record_type,
        record_id=request.record_id,
        pipeline_id=request.pipeline_id,
        pipeline_stage_id=request.pipeline_stage_id,
        list_id=request.list_id,
        trigger_event=request.trigger_event,
        condition_json=request.condition_json,
        action_type=request.action_type,
        config_json=request.config_json,
        priority=request.priority or 1,
        enabled=request.enabled if request.enabled is not None else True,
        inherit_pipeline_actions=request.inherit_pipeline_actions if request.inherit_pipeline_actions is not None else True,
        created_by_user_id=created_by,
        updated_by_user_id=created_by,
    )
    db.add(action)
    commit_or_raise(db, refresh=action, action="create automation action")
    snapshot = _snapshot(action)
    try:
        AutomationActionProducer.send_automation_action_created(
            tenant_id=tenant_id, payload=snapshot
        )
    except Exception:
        # Suppress messaging errors; classification handled by messaging layer
        pass
    return action


def get_automation_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
) -> AutomationAction:
    """Retrieve an automation action by ID within a tenant context."""
    action = (
        db.query(AutomationAction)
        .filter(
            AutomationAction.id == action_id,
            AutomationAction.tenant_id == tenant_id,
        )
        .first()
    )
    if not action:
        logger.info(
            "Automation action not found: tenant_id=%s, id=%s", tenant_id, action_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation action not found")
    return action


def update_automation_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
    request: AutomationActionUpdate,
    updated_by: str,
) -> AutomationAction:
    """Update an existing automation action and publish an update event."""
    action = get_automation_action(db, tenant_id=tenant_id, action_id=action_id)
    updates: Dict[str, Any] = {}
    # Determine which fields have been supplied; ignore None
    for field in [
        "entity_type",
        "scope_type",
        "record_type",
        "record_id",
        "pipeline_id",
        "pipeline_stage_id",
        "list_id",
        "trigger_event",
        "condition_json",
        "action_type",
        "config_json",
        "priority",
        "enabled",
        "inherit_pipeline_actions",
    ]:
        value = getattr(request, field)
        if value is not None:
            updates[field] = value
    delta = _compute_delta(action, updates)
    if delta.base_fields:
        for field, value in delta.base_fields.items():
            setattr(action, field, value)
        action.updated_by_user_id = updated_by
        action.updated_at = datetime.utcnow()
        commit_or_raise(db, refresh=action, action="update automation action")
        snapshot = _snapshot(action)
        try:
            AutomationActionProducer.send_automation_action_updated(
                tenant_id=tenant_id,
                changes=delta,
                payload=snapshot,
            )
        except Exception:
            pass
    return action


def delete_automation_action(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    action_id: uuid.UUID,
) -> None:
    """Delete an automation action and publish a deletion event."""
    action = get_automation_action(db, tenant_id=tenant_id, action_id=action_id)
    db.delete(action)
    commit_or_raise(db, action="delete automation action")
    deleted_dt = datetime.utcnow().isoformat()
    try:
        AutomationActionProducer.send_automation_action_deleted(
            tenant_id=tenant_id,
            deleted_dt=deleted_dt,
        )
    except Exception:
        pass
    return None


__all__ = [
    "list_automation_actions",
    "create_automation_action",
    "get_automation_action",
    "update_automation_action",
    "delete_automation_action",
]