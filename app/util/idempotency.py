"""
Helpers for implementing idempotent event consumption.

The idempotency pattern uses a ``processed_message`` table to track
which messages have already been processed by a given consumer.
Consumers should call ``record_message_processed`` at the start of
their task logic; if the call returns ``False`` then the message has
already been handled and the consumer should return early.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.models.processed_message import ProcessedMessage


def record_message_processed(
    db: Session, tenant_id: UUID, message_id: UUID, consumer_name: str
) -> bool:
    """
    Persist a record that a message has been processed by this consumer.

    Returns ``True`` if the record was inserted and the caller should
    proceed with processing. Returns ``False`` if a unique constraint
    violation occurs, indicating that the message has already been
    processed.

    Args:
        db: SQLAlchemy session
        tenant_id: Tenant identifier
        message_id: The unique event identifier from the message envelope
        consumer_name: Name of the consumer/task handling the message

    Returns:
        bool: ``True`` if the message should be processed, ``False`` if
        it has already been processed.
    """
    processed = ProcessedMessage(
        tenant_id=tenant_id,
        message_id=message_id,
        consumer_name=consumer_name,
    )
    db.add(processed)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False