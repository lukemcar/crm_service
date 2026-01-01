"""SQLAlchemy model for Activity.

Represents notes and tasks associated with CRM records.  Activities are
polymorphic, with a `type` field to distinguish notes vs tasks.  Tasks
have additional properties like due_date, status and assigned_user_id.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Text, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Activity(Base):
    __tablename__ = "activities"
    
    __table_args__ = (
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'note' or 'task'
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'open', 'completed'
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<Activity id={self.id} type={self.type} title={self.title}>"