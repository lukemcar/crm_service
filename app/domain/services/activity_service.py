"""Service layer for Activity operations.

This module follows the canonical service pattern established in the CRM for
domain models.  It provides tenant‑scoped and admin‑scoped CRUD operations
for activities and publishes lifecycle events through the messaging layer.
All database writes are committed via ``commit_or_raise`` to centralize
error handling, and events are emitted only after a successful commit.
Audit fields (`created_by` and `updated_by`) are strings derived from the
``X-User`` header.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, List, Tuple, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.activity import Activity
from app.domain.schemas.activity import ActivityCreate, ActivityUpdate, ActivityRead
from app.domain.services.common_service import commit_or_raise
# Import the canonical activity message producer.  This class publishes events
# after successful commits and should be used for all activity lifecycle
# notifications.  See app/messaging/producers/activity_producer.py for details.
from app.messaging.producers.activity_producer import ActivityMessageProducer


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _activity_snapshot(activity: Activity) -> Dict[str, Any]:
    """Return a dictionary snapshot of the activity for event payloads."""
    read_model = ActivityRead.model_validate(activity, from_attributes=True)
    return read_model.model_dump()


def list_activities(
    db: Session,
    *,
    tenant_id: UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[Activity], int]:
    """Return a list of activities for a given tenant with optional pagination and filters.

    Parameters
    ----------
    tenant_id: UUID
        Tenant identifier used to scope the query.
    limit: Optional[int]
        Maximum number of records to return.
    offset: Optional[int]
        Number of records to skip from the beginning.
    type: Optional[str]
        Optional filter by activity type.
    status: Optional[str]
        Optional filter by activity status.

    Returns
    -------
    (activities, total): Tuple[List[Activity], int]
        A tuple containing the list of activities and the total count before pagination.
    """
    query = db.query(Activity).filter(Activity.tenant_id == tenant_id)
    if type:
        query = query.filter(Activity.type.ilike(type))
    if status:
        query = query.filter(Activity.status.ilike(status))
    total = query.count()
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    activities = query.all()
    return activities, total


def get_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_id: UUID,
) -> Activity:
    """Fetch a single activity by ID within the tenant.

    Raises HTTP 404 if the activity does not exist or does not belong to the tenant.
    """
    activity: Optional[Activity] = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.tenant_id == tenant_id)
        .first()
    )
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    return activity


def create_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_in: ActivityCreate,
    created_user: str,
) -> Activity:
    """Create a new activity for the tenant.

    All writes are committed via ``commit_or_raise`` and the creation event is
    published after a successful commit.
    """
    activity = Activity(
        tenant_id=tenant_id,
        type=activity_in.type,
        title=activity_in.title,
        description=activity_in.description,
        due_date=activity_in.due_date,
        status=activity_in.status,
        assigned_user_id=activity_in.assigned_user_id,
        created_by=created_user,
        updated_by=created_user,
    )
    db.add(activity)
    commit_or_raise(db, refresh=activity, action="create activity")
    snapshot = _activity_snapshot(activity)
    try:
        ActivityMessageProducer.send_activity_created(
            tenant_id=tenant_id,
            payload=snapshot,
        )
    except Exception:
        import logging
        logger = logging.getLogger("activity_service")
        logger.exception(
            "Failed to publish activity.created event tenant_id=%s activity_id=%s",
            tenant_id,
            activity.id,
        )
    return activity


def update_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_id: UUID,
    activity_in: ActivityUpdate,
    modified_user: str,
) -> Activity:
    """Update an existing activity with provided fields.

    Only provided fields are modified; unspecified fields remain unchanged.
    The update is committed via ``commit_or_raise``, and an update event is
    published if any changes occur.
    """
    activity = get_activity(db, tenant_id=tenant_id, activity_id=activity_id)
    original = {
        "type": activity.type,
        "title": activity.title,
        "description": activity.description,
        "due_date": activity.due_date,
        "status": activity.status,
        "assigned_user_id": activity.assigned_user_id,
    }
    if activity_in.type is not None:
        activity.type = activity_in.type
    if activity_in.title is not None:
        activity.title = activity_in.title
    if activity_in.description is not None:
        activity.description = activity_in.description
    if activity_in.due_date is not None:
        activity.due_date = activity_in.due_date
    if activity_in.status is not None:
        activity.status = activity_in.status
    if activity_in.assigned_user_id is not None:
        activity.assigned_user_id = activity_in.assigned_user_id
    activity.updated_by = modified_user
    activity.updated_at = datetime.utcnow()
    db.add(activity)
    commit_or_raise(db, refresh=activity, action="update activity")
    changes: Dict[str, Any] = {}
    if original["type"] != activity.type:
        changes["type"] = activity.type
    if original["title"] != activity.title:
        changes["title"] = activity.title
    if original["description"] != activity.description:
        changes["description"] = activity.description
    if original["due_date"] != activity.due_date:
        changes["due_date"] = activity.due_date
    if original["status"] != activity.status:
        changes["status"] = activity.status
    if original["assigned_user_id"] != activity.assigned_user_id:
        changes["assigned_user_id"] = activity.assigned_user_id
    if changes:
        snapshot = _activity_snapshot(activity)
        try:
            ActivityMessageProducer.send_activity_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=snapshot,
            )
        except Exception:
            import logging
            logger = logging.getLogger("activity_service")
            logger.exception(
                "Failed to publish activity.updated event tenant_id=%s activity_id=%s",
                tenant_id,
                activity.id,
            )
    return activity


def delete_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_id: UUID,
) -> None:
    """Delete the specified activity and publish a deletion event."""
    activity = get_activity(db, tenant_id=tenant_id, activity_id=activity_id)
    db.delete(activity)
    commit_or_raise(db, action="delete activity")
    try:
        ActivityMessageProducer.send_activity_deleted(
            tenant_id=tenant_id,
            deleted_dt=None,
        )
    except Exception:
        import logging
        logger = logging.getLogger("activity_service")
        logger.exception(
            "Failed to publish activity.deleted event tenant_id=%s activity_id=%s",
            tenant_id,
            activity.id,
        )


def service_list_activities(
    db: Session,
    *,
    tenant_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[Activity], int]:
    """Admin variant of list_activities that optionally scopes by tenant.

    If ``tenant_id`` is ``None``, activities across all tenants are returned.
    """
    query = db.query(Activity)
    if tenant_id is not None:
        query = query.filter(Activity.tenant_id == tenant_id)
    if type:
        query = query.filter(Activity.type.ilike(type))
    if status:
        query = query.filter(Activity.status.ilike(status))
    total = query.count()
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    activities = query.all()
    return activities, total


def service_create_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_in: ActivityCreate,
    created_user: str,
) -> Activity:
    """Admin variant of create_activity.  Delegates to the tenant‑scoped variant."""
    return create_activity(
        db=db,
        tenant_id=tenant_id,
        activity_in=activity_in,
        created_user=created_user,
    )


def service_update_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_id: UUID,
    activity_in: ActivityUpdate,
    modified_user: str,
) -> Activity:
    """Admin variant of update_activity.  Delegates to the tenant‑scoped variant."""
    return update_activity(
        db=db,
        tenant_id=tenant_id,
        activity_id=activity_id,
        activity_in=activity_in,
        modified_user=modified_user,
    )


def service_delete_activity(
    db: Session,
    *,
    tenant_id: UUID,
    activity_id: UUID,
) -> None:
    """Admin variant of delete_activity.  Delegates to the tenant‑scoped variant."""
    delete_activity(
        db=db,
        tenant_id=tenant_id,
        activity_id=activity_id,
    )