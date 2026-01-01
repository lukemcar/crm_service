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
from typing import Optional

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Association(Base):
    __tablename__ = "associations"
    
    __table_args__ = (
        {"schema": "dyno_crm"},
    )

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

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Association id={self.id} tenant_id={self.tenant_id} "
            f"from={self.from_object_type}:{self.from_object_id} "
            f"to={self.to_object_type}:{self.to_object_id} type={self.association_type}>"
        )
        
        
'''
Yes, but not in the way people hope at first.

With a `(table_name, object_id)` polymorphic reference you cannot have a real SQL foreign key, so SQLAlchemy cannot build a normal `relationship()` that joins to “whatever table the string says” without you doing some custom plumbing.

You have three practical options.

## Option A: Keep it generic, add a resolver (recommended)

Treat `associations` as a pure link table and provide a small registry that maps `object_type -> mapped class`, then resolve targets on demand.

Pros: simple, explicit, works great with many types, no mapper magic.
Cons: not a lazy-loaded relationship; you resolve explicitly.

### `app/domain/models/association.py` (updated with resolver helpers)

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Type

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base


class Association(Base):
    __tablename__ = "associations"
    __table_args__ = (
        Index("ix_associations_tenant", "tenant_id"),
        Index("ix_associations_from", "from_object_id"),
        Index("ix_associations_to", "to_object_id"),
        {"schema": "dyno_crm"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    from_object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_object_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    to_object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    to_object_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    association_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # ---- Resolution helpers (no ORM relationship here) ----

    def resolve_from(self, db: Session, registry: Dict[str, Type[Any]]) -> Any | None:
        model = registry.get(self.from_object_type)
        if model is None:
            return None
        return db.get(model, self.from_object_id)

    def resolve_to(self, db: Session, registry: Dict[str, Type[Any]]) -> Any | None:
        model = registry.get(self.to_object_type)
        if model is None:
            return None
        return db.get(model, self.to_object_id)

    def __repr__(self) -> str:
        return (
            f"<Association id={self.id} tenant_id={self.tenant_id} "
            f"from={self.from_object_type}:{self.from_object_id} "
            f"to={self.to_object_type}:{self.to_object_id} type={self.association_type}>"
        )
```

### Example registry (central place, imported at startup)

```python
# app/domain/association_registry.py
from app.domain.models.company import Company
from app.domain.models.contact import Contact
from app.domain.models.deal import Deal

ASSOCIATION_TYPE_REGISTRY = {
    "companies": Company,
    "contacts": Contact,
    "deals": Deal,
}
```

This is the cleanest approach in a system like yours where new tables will appear over time.

---

## Option B: “GenericForeignKey” style via custom join conditions (possible, but messy)

You *can* define view-only relationships per target type using `primaryjoin` with a constant discriminator, like:

* `Association.from_deal` relationship joins only when `from_object_type == "deals"`
* `Association.to_company` joins only when `to_object_type == "companies"`

Pros: you get real `relationship()` objects.
Cons: you need one relationship attribute per type, and you must update models each time you add a new entity.

Example snippet (illustrative):

```python
from sqlalchemy.orm import foreign
from sqlalchemy import and_

from_deal = relationship(
    "Deal",
    primaryjoin=lambda: and_(
        foreign(Association.from_object_id) == Deal.id,
        Association.from_object_type == "deals",
    ),
    viewonly=True,
)
```

This works, but it scales poorly if your CRM will have many entity types.

---

## Option C: Redesign to “supertype table” (most relational, least flexible)

If you want real FK integrity and simple ORM relationships, you create a canonical table like `crm_objects(id, tenant_id, object_type, ...)` and every entity has a 1:1 row there, then `associations.from_object_id` FK to `crm_objects.id`.

Pros: real FK constraints, simple joins, excellent integrity.
Cons: more schema work, more write complexity, more migrations.

---

## My recommendation for DYNO CRM

Use **Option A** (registry + resolver) for now. It keeps your schema flexible and your ORM sane. If later you want stronger integrity, move to Option C.

If you tell me which entity types you want to support first (company, contact, deal, ticket, pipeline?), I can generate:

* the registry file,
* helper query functions like `list_links_for_object(db, tenant_id, table_name, object_id)`,
* and a service layer pattern that returns fully-resolved objects efficiently (batch loads instead of N+1).

'''