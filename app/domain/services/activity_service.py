"""Service layer for Activity operations.

Provides CRUD operations for activities, which capture notes and
tasks associated with CRM records.  Activities are scoped by
tenant; all queries filter by tenant_id.  Consumers of this
service may implement additional filtering (e.g., by object ID)
around these functions if needed.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.activity import Activity
from app.domain.schemas.activity import ActivityCreate, ActivityUpdate


def list_activities(db: Session, tenant_id: uuid.UUID) -> Iterable[Activity]:
    """Return all activities for a given tenant."""
    return db.query(Activity).filter(Activity.tenant_id == tenant_id).all()


def get_activity(db: Session, activity_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Activity]:
    """Fetch a single activity by ID within the tenant."""
    return (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.tenant_id == tenant_id)
        .first()
    )


def create_activity(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    activity_in: ActivityCreate,
) -> Activity:
    """Create a new activity for the tenant."""
    activity = Activity(
        tenant_id=tenant_id,
        type=activity_in.type,
        title=activity_in.title,
        description=activity_in.description,
        due_date=activity_in.due_date,
        status=activity_in.status,
        assigned_user_id=activity_in.assigned_user_id,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def update_activity(
    db: Session,
    activity: Activity,
    user_id: Optional[uuid.UUID],
    activity_in: ActivityUpdate,
) -> Activity:
    """Update an existing activity with provided fields."""
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
    activity.updated_by = user_id
    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity: Activity) -> None:
    """Delete the specified activity."""
    db.delete(activity)
    db.commit()