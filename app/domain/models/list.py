"""SQLAlchemy model for List (Segment).

Represents a saved segment of CRM records.  Lists are tenant scoped and
support static and snapshot types.  Memberships are stored in the
ListMembership table.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class List(Base):
    __tablename__ = "lists"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    list_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filter_definition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Relationship to list memberships
    memberships: Mapped[list["ListMembership"]] = relationship(
        "ListMembership",
        back_populates="list",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<List id={self.id} name={self.name} type={self.list_type}>"