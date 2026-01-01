"""SQLAlchemy model for CSAT (Customer Satisfaction) responses.

This table stores individual responses to customer satisfaction surveys
linked to tickets. Each response captures the rating (1..5), an optional
comment, and references to the survey, ticket, and contact who
responded. Responses are tenant scoped. Updates and deletes are
restricted to administrative corrections.
"""

import datetime as _dt
import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
    Index,
    String,
    Integer,
    Text,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class CsatResponse(Base):
    """Model for the ``csat_response`` table."""

    __tablename__ = "csat_response"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="ux_csat_response_id_tenant"),
        # Composite foreign key linking survey and tenant for tenant safety
        ForeignKeyConstraint(
            ["csat_survey_id", "tenant_id"],
            ["csat_survey.id", "csat_survey.tenant_id"],
            ondelete="SET NULL",
            name="fk_csat_response_survey_tenant",
        ),
        # Composite foreign key linking ticket and tenant
        ForeignKeyConstraint(
            ["ticket_id", "tenant_id"],
            ["ticket.id", "ticket.tenant_id"],
            ondelete="CASCADE",
            name="fk_csat_response_ticket_tenant",
        ),
        # Composite foreign key linking contact and tenant
        ForeignKeyConstraint(
            ["contact_id", "tenant_id"],
            ["contact.id", "contact.tenant_id"],
            ondelete="SET NULL",
            name="fk_csat_response_contact_tenant",
        ),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_csat_rating"),
        Index("ix_csat_response_tenant_ticket", "tenant_id", "ticket_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    # Survey is optional (responses can exist without explicit survey)
    csat_survey_id = Column(UUID(as_uuid=True), nullable=True)
    ticket_id = Column(UUID(as_uuid=True), nullable=False)
    contact_id = Column(UUID(as_uuid=True), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=_dt.datetime.utcnow)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_dt.datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<CsatResponse id={self.id} tenant={self.tenant_id} ticket={self.ticket_id} rating={self.rating}>"


__all__ = ["CsatResponse"]