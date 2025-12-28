"""Service layer for Association operations.

Associations enable arbitrary relationships between any two CRM
entities.  Each association is scoped to a tenant and records
both sides of the link along with an optional association type.
This module provides functions to list, create and delete
associations.  Updates are not supported; clients should delete and
recreate associations as needed.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.domain.models.association import Association
from app.domain.schemas.association import AssociationCreate


def list_associations(db: Session, tenant_id: uuid.UUID) -> Iterable[Association]:
    """Return all associations for a given tenant."""
    return db.query(Association).filter(Association.tenant_id == tenant_id).all()


def get_association(db: Session, association_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Association]:
    """Fetch a single association by ID within the tenant."""
    return (
        db.query(Association)
        .filter(Association.id == association_id, Association.tenant_id == tenant_id)
        .first()
    )


def create_association(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    association_in: AssociationCreate,
) -> Association:
    """Create a new association for the tenant."""
    assoc = Association(
        tenant_id=tenant_id,
        from_object_type=association_in.from_object_type,
        from_object_id=association_in.from_object_id,
        to_object_type=association_in.to_object_type,
        to_object_id=association_in.to_object_id,
        association_type=association_in.association_type,
        created_by=user_id,
    )
    db.add(assoc)
    db.commit()
    db.refresh(assoc)
    return assoc


def delete_association(db: Session, association: Association) -> None:
    """Delete the specified association."""
    db.delete(association)
    db.commit()