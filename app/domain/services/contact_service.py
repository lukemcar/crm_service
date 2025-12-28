"""Service layer for Contact operations.

Encapsulates database interactions and business logic for creating,
retrieving, updating and deleting contacts.  All functions assume
tenant scoping; they filter by tenant_id to enforce multi‑tenancy.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.contact import Contact
from app.domain.schemas.contact import ContactCreate, ContactUpdate


def list_contacts(db: Session, tenant_id: uuid.UUID) -> Iterable[Contact]:
    """Return all contacts for the given tenant."""
    return db.query(Contact).filter(Contact.tenant_id == tenant_id).all()


def get_contact(db: Session, contact_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Contact]:
    """Fetch a single contact by ID within the tenant."""
    return (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.tenant_id == tenant_id)
        .first()
    )


def create_contact(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    contact_in: ContactCreate,
) -> Contact:
    """Create a new contact in the given tenant."""
    contact = Contact(
        tenant_id=tenant_id,
        first_name=contact_in.first_name,
        last_name=contact_in.last_name,
        email=contact_in.email,
        phone=contact_in.phone,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(
    db: Session,
    contact: Contact,
    user_id: Optional[uuid.UUID],
    contact_in: ContactUpdate,
) -> Contact:
    """Update an existing contact.  Only provided fields are updated."""
    if contact_in.first_name is not None:
        contact.first_name = contact_in.first_name
    if contact_in.last_name is not None:
        contact.last_name = contact_in.last_name
    if contact_in.email is not None:
        contact.email = contact_in.email
    if contact_in.phone is not None:
        contact.phone = contact_in.phone
    contact.updated_by = user_id
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact: Contact) -> None:
    """Delete the contact.  For now perform a hard delete."""
    db.delete(contact)
    db.commit()