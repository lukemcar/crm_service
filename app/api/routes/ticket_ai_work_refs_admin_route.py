"""
Admin FastAPI routes for ticket AI work references.

These endpoints allow administrators or internal services to list,
upsert and delete AI work reference records across tenants. Listing
supports optional scoping by tenant and ticket identifiers. Upsert
operations require a ``tenant_id`` and ``ticket_id`` in the request
body to ensure that the operation is applied within the correct
tenant context. Audit fields (created_by/updated_by) are populated
from the ``X-User`` header when provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_ai_work_ref_service import (
    list_ticket_ai_work_refs as service_list_ai_work_refs,
    upsert_ticket_ai_work_ref as service_upsert_ai_work_ref,
    get_ticket_ai_work_ref as service_get_ai_work_ref,
    delete_ticket_ai_work_ref as service_delete_ai_work_ref,
)
from app.domain.schemas.ticket_ai_work_ref import (
    AdminUpsertTicketAiWorkRef,
    TicketAiWorkRefOut,
)
from app.domain.schemas.common import PaginationEnvelope

import uuid


router = APIRouter(
    prefix="/admin/ticket_ai_work_refs",
    tags=["TicketAiWorkRefs"],
)


@router.get("/", response_model=PaginationEnvelope[TicketAiWorkRefOut])
def list_ticket_ai_work_refs_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None, description="Optional tenant ID to scope the search"
    ),
    ticket_id: Optional[UUID] = Query(
        None, description="Optional ticket ID to further scope the search"
    ),
    agent_key: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketAiWorkRefOut]:
    """List ticket AI work references across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant. If
    ``ticket_id`` is also provided, results are scoped to a single
    ticket. Agent key filtering and pagination are supported.
    """
    refs, total = service_list_ai_work_refs(
        db,
        tenant_id=tenant_id if tenant_id else uuid.UUID(int=0),
        ticket_id=ticket_id,
        agent_key=agent_key,
        limit=limit,
        offset=offset,
    )
    items: List[TicketAiWorkRefOut] = [
        TicketAiWorkRefOut.model_validate(r, from_attributes=True) for r in refs
    ]
    return PaginationEnvelope[TicketAiWorkRefOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.put("/{ref_id}", response_model=TicketAiWorkRefOut)
def upsert_ticket_ai_work_ref_admin(
    *,
    ref_id: UUID,
    request: AdminUpsertTicketAiWorkRef,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketAiWorkRefOut:
    """Upsert a ticket AI work reference record as an admin.

    The ``ref_id`` path parameter identifies the record to update. The
    request body must include ``tenant_id`` and ``ticket_id``. If the
    record does not exist, it will be created. The ``X-User`` header
    supplies the audit identity; defaults to ``"anonymous"``.
    """
    updated_user = x_user or "anonymous"
    request_dict = request.model_dump()
    request_dict["id"] = ref_id
    req = AdminUpsertTicketAiWorkRef(**request_dict)
    ref = service_upsert_ai_work_ref(
        db,
        tenant_id=req.tenant_id,
        request=req,
        updated_by=updated_user,
    )
    return TicketAiWorkRefOut.model_validate(ref, from_attributes=True)


@router.get("/{ref_id}", response_model=TicketAiWorkRefOut)
def get_ticket_ai_work_ref_admin(
    *,
    ref_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the AI work reference to retrieve"
    ),
    db: Session = Depends(get_db),
) -> TicketAiWorkRefOut:
    """Retrieve a ticket AI work reference across tenants.

    The ``tenant_id`` query parameter is required to ensure that the
    operation is scoped to the correct tenant.
    """
    ref = service_get_ai_work_ref(db, tenant_id=tenant_id, ref_id=ref_id)
    return TicketAiWorkRefOut.model_validate(ref, from_attributes=True)


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_ai_work_ref_admin(
    *,
    ref_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the AI work reference to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket AI work reference as an admin."""
    service_delete_ai_work_ref(
        db,
        tenant_id=tenant_id,
        ref_id=ref_id,
    )
    return None