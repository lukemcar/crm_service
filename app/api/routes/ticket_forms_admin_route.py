"""
Admin FastAPI routes for ticket forms.

These endpoints allow administrators to list, create, update, retrieve
and delete ticket forms across tenants.  Listing supports optional
tenant scoping to a single tenant.  Create and mutation operations
require an explicit ``tenant_id`` in the request body or query
parameter to ensure that the operation applies within the correct
tenant.  Audit fields are populated from the ``X-User`` header when
provided.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_form_service import (
    list_ticket_forms as service_list_ticket_forms,
    create_ticket_form as service_create_ticket_form,
    update_ticket_form as service_update_ticket_form,
    get_ticket_form as service_get_ticket_form,
    delete_ticket_form as service_delete_ticket_form,
)
from app.domain.schemas.ticket_form import (
    AdminCreateTicketForm,
    TicketFormUpdate,
    TicketFormOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/ticket_forms",
    tags=["TicketForms"],
)


@router.get("/", response_model=PaginationEnvelope[TicketFormOut])
def list_ticket_forms_admin(
    *,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional tenant ID to scope the search to a single tenant",
    ),
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketFormOut]:
    """List or search ticket forms across tenants.

    If ``tenant_id`` is provided, results are scoped to that tenant.
    The ``is_active`` filter performs an exact match on the active flag.
    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  The total matching count is included.
    """
    forms, total = service_list_ticket_forms(
        db,
        tenant_id=tenant_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items: List[TicketFormOut] = [
        TicketFormOut.model_validate(f, from_attributes=True) for f in forms
    ]
    return PaginationEnvelope[TicketFormOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=TicketFormOut, status_code=status.HTTP_201_CREATED)
def create_ticket_form_admin(
    *,
    form_in: AdminCreateTicketForm,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFormOut:
    """Create a new ticket form on behalf of a tenant.

    Admin callers must supply ``tenant_id`` in the request body via
    ``AdminCreateTicketForm``.  The ``X-User`` header is used
    for audit purposes; if omitted, ``created_by`` and ``updated_by``
    are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    form = service_create_ticket_form(
        db,
        tenant_id=form_in.tenant_id,
        request=form_in,
        created_by=created_user,
    )
    return TicketFormOut.model_validate(form, from_attributes=True)


@router.patch("/{form_id}", response_model=TicketFormOut)
def update_ticket_form_admin(
    *,
    form_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form to update"
    ),
    form_update: TicketFormUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFormOut:
    """Apply updates to a ticket form as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    operation applies within the correct tenant.  Only fields provided
    in the request are updated.
    """
    updated_user = x_user or "anonymous"
    form = service_update_ticket_form(
        db,
        tenant_id=tenant_id,
        form_id=form_id,
        request=form_update,
        updated_by=updated_user,
    )
    return TicketFormOut.model_validate(form, from_attributes=True)


@router.get("/{form_id}", response_model=TicketFormOut)
def get_ticket_form_admin(
    *,
    form_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form to retrieve"
    ),
    db: Session = Depends(get_db),
) -> TicketFormOut:
    """Retrieve a ticket form across tenants.

    An explicit ``tenant_id`` query parameter is required so that the
    form can be resolved in the correct tenant context.  Raises 404
    if the form does not exist in the tenant.
    """
    form = service_get_ticket_form(
        db, tenant_id=tenant_id, form_id=form_id
    )
    return TicketFormOut.model_validate(form, from_attributes=True)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_form_admin(
    *,
    form_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form to delete"
    ),
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket form as an admin.

    The ``tenant_id`` query parameter is required to ensure that the
    deletion occurs within the correct tenant.  Returns HTTP 204 on
    success.  Event publishers do not include user information for
    deletions.
    """
    service_delete_ticket_form(
        db, tenant_id=tenant_id, form_id=form_id
    )
    return None