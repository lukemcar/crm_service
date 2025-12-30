"""SQLAlchemy model for ListMembership.

Represents a membership record linking a list to a particular record of a given type.
The table is used to store static or snapshot lists, where each member of the list
is identified by its UUID and type (e.g. contact, company, deal).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ListMembership(Base):
    __tablename__ = "list_memberships"
    __table_args__ = (
        Index("ix_list_memberships_list", "list_id"),
        Index("ix_list_memberships_member", "member_id"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # IMPORTANT: schema-qualified FK because lists live in dyno_crm schema
    list_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dyno_crm.lists.id", ondelete="CASCADE"),
        nullable=False,
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    member_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    list: Mapped["List"] = relationship(
        "List",
        back_populates="memberships",
    )

    def __repr__(self) -> str:
        return f"<ListMembership id={self.id} list_id={self.list_id} member={self.member_type}:{self.member_id}>"
