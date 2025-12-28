"""SQLAlchemy model for ListMembership.

Represents a membership record linking a list to a particular record of a given type.
The table is used to store static or snapshot lists, where each member of the list
is identified by its UUID and type (e.g. contact, company, deal).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ListMembership(Base):
    __tablename__ = "list_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    list_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("lists.id", ondelete="CASCADE"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    member_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Relationship back to parent list
    list: Mapped["List"] = relationship(
        "List",
        back_populates="memberships",
    )

    def __repr__(self) -> str:
        return (
            f"<ListMembership id={self.id} list_id={self.list_id} "
            f"member_id={self.member_id} member_type={self.member_type}>"
        )