"""
Tenant‑scoped FastAPI routes for ticket forms.

These endpoints allow tenants to list, create, update, retrieve and
delete custom ticket forms that belong to them.  A filter is provided
for active status.  Audit fields are populated from the ``X-User``
header when provided; otherwise "anonymous" is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
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
    TenantCreateTicketForm,
    TicketFormUpdate,
    TicketFormOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/ticket_forms",
    tags=["TicketForms"],
)


@router.get("/", response_model=PaginationEnvelope[TicketFormOut])
def list_ticket_forms_endpoint(
    tenant_id: UUID,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketFormOut]:
    """List ticket forms for a tenant with an optional active filter.

    Results are ordered by creation date descending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of forms.
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
def create_ticket_form_endpoint(
    tenant_id: UUID,
    form_in: TenantCreateTicketForm,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFormOut:
    """Create a new ticket form for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` fields on
    the form are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    form = service_create_ticket_form(
        db,
        tenant_id=tenant_id,
        request=form_in,
        created_by=created_user,
    )
    return TicketFormOut.model_validate(form, from_attributes=True)


@router.patch("/{form_id}", response_model=TicketFormOut)
def update_ticket_form_endpoint(
    tenant_id: UUID,
    form_id: UUID,
    form_update: TicketFormUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFormOut:
    """Update an existing ticket form.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
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
def get_ticket_form_endpoint(
    tenant_id: UUID,
    form_id: UUID,
    db: Session = Depends(get_db),
) -> TicketFormOut:
    """Retrieve a single ticket form by ID within a tenant.

    Raises 404 if the form does not exist or does not belong to
    the tenant.
    """
    form = service_get_ticket_form(
        db, tenant_id=tenant_id, form_id=form_id
    )
    return TicketFormOut.model_validate(form, from_attributes=True)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_form_endpoint(
    tenant_id: UUID,
    form_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket form from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the form does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events; event publishers
    do not include user information for deletions.
    """
    service_delete_ticket_form(
        db, tenant_id=tenant_id, form_id=form_id
    )
    return None