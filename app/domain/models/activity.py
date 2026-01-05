"""SQLAlchemy model for Activity.

Represents notes and tasks associated with CRM records.  Activities are
polymorphic, with a `type` field to distinguish notes vs tasks.  Tasks
have additional properties like due_date, status and assigned_user_id.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Text, Date, DateTime, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Activity(Base):
    """SQLAlchemy model for Activity.

    Represents notes and tasks associated with CRM records.  Activities are
    polymorphic, with an ``activity_type`` field to distinguish notes vs tasks.
    Additional metadata such as when the activity occurred (``activity_at``),
    ownership/assignment information and free‑form details JSON have been added
    to align with the consolidated CRM change request【175114821575405†L1408-L1450】.
    """

    __tablename__ = "activities"

    #
    # Composite table arguments including schema and foreign key constraints.
    #
    # The schema specification must appear alongside foreign key constraints in
    # a single tuple; otherwise, subsequent assignments override earlier ones.
    # The two ForeignKeyConstraint definitions below ensure that the
    # ``created_by_user_id`` and ``assigned_group_id`` columns form composite
    # keys with ``tenant_id`` against the tenant shadow tables.  When a
    # referenced user or group is deleted, the corresponding field on the
    # activity is set to NULL (ondelete="SET NULL").
    __table_args__ = (
        # Foreign key to tenant_user_shadow on (tenant_id, created_by_user_id)
        ForeignKeyConstraint(
            ["tenant_id", "created_by_user_id"],
            ["dyno_crm.tenant_user_shadow.tenant_id", "dyno_crm.tenant_user_shadow.user_id"],
            ondelete="SET NULL",
        ),
        # Foreign key to tenant_group_shadow on (tenant_id, assigned_group_id)
        ForeignKeyConstraint(
            ["tenant_id", "assigned_group_id"],
            ["dyno_crm.tenant_group_shadow.tenant_id", "dyno_crm.tenant_group_shadow.id"],
            ondelete="SET NULL",
        ),
        # Schema specification
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    # Rename ``type`` to ``activity_type`` per the implementation guide【175114821575405†L1418-L1434】.
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Optional human readable title
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Long form description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When the activity is due (for tasks).  Unchanged from prior model.
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Current status of the activity.  Examples: 'open', 'completed'.
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Existing assignment by user ID
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    # New assignment by group ID【175114821575405†L1439-L1443】
    assigned_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    # Timestamp when the activity occurred【175114821575405†L1434-L1437】
    activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # User ID of the creator (tenant_user_shadow FK)【175114821575405†L1434-L1443】
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    # Additional structured details (JSON)【175114821575405†L1439-L1444】
    # Structured details stored as JSON; use PGJSONB for Postgres support
    details_json: Mapped[dict | None] = mapped_column(
        PGJSONB(astext_type=String()), nullable=True
    )
    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Legacy string audit fields remain for backwards compatibility
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<Activity id={self.id} activity_type={self.activity_type} title={self.title}>"

    # Placeholder for mapper configuration; no custom mapper args at this time.
    __mapper_args__ = {}