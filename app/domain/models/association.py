"""SQLAlchemy model for Association.

This table stores generic associations between any two CRM records.  It enables
many‑to‑many relationships across entity types without explicit foreign keys
to individual tables.  Each association is scoped to a tenant and records
both sides of the link along with an optional association type (e.g. primary,
secondary).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Association(Base):
    __tablename__ = "associations"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    from_object_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    from_object_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    to_object_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    to_object_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    association_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<Association id={self.id} tenant_id={self.tenant_id} "
            f"from={self.from_object_type}:{self.from_object_id} "
            f"to={self.to_object_type}:{self.to_object_id} type={self.association_type}>"
        )