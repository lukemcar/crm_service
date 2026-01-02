"""Administrative endpoints for the DYNO CRM service.

These endpoints expose read-only projections over internal data
structures for administrative or diagnostic purposes.  In a real
application, these would be protected by appropriate authorisation
checks.  For now they are open for simplicity.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.models import Contact

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tenants", response_model=List[UUID], summary="List tenant identifiers")
def list_tenants(db: Session = Depends(get_db)) -> List[UUID]:
    """Return a list of unique tenant identifiers present in the system.

    The current implementation inspects the Contact table to infer
    tenant IDs.  In the future, a dedicated Tenant table or
    projection might be used.
    """
    result = db.execute(select(Contact.tenant_id).distinct())
    tenant_ids = [row[0] for row in result]
    return tenant_ids