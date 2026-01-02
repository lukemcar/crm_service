"""
Tenant‑scoped FastAPI routes for ticket form fields.

These endpoints allow tenants to list, create, update, retrieve and
delete associations between ticket forms and custom field definitions.
Optional filters provide the ability to narrow results by form or field
definition.  Audit fields are populated from the ``X-User`` header
when provided; otherwise "anonymous" is used.  Only the display order
can be updated after creation.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services.ticket_form_field_service import (
    list_ticket_form_fields as service_list_ticket_form_fields,
    create_ticket_form_field as service_create_ticket_form_field,
    update_ticket_form_field as service_update_ticket_form_field,
    get_ticket_form_field as service_get_ticket_form_field,
    delete_ticket_form_field as service_delete_ticket_form_field,
)
from app.domain.schemas.ticket_form_field import (
    TenantCreateTicketFormField,
    TicketFormFieldUpdate,
    TicketFormFieldOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/tenants/{tenant_id}/ticket_form_fields",
    tags=["TicketFormFields"],
)


@router.get("/", response_model=PaginationEnvelope[TicketFormFieldOut])
def list_ticket_form_fields_endpoint(
    tenant_id: UUID,
    ticket_form_id: Optional[UUID] = None,
    ticket_field_def_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketFormFieldOut]:
    """List ticket form fields for a tenant with optional filters.

    Results are ordered by display order ascending and wrapped in a
    pagination envelope.  Passing ``limit`` or ``offset`` will page
    results accordingly.  The total count of records matching the
    criteria is returned alongside the list of form fields.
    """
    fields, total = service_list_ticket_form_fields(
        db,
        tenant_id=tenant_id,
        ticket_form_id=ticket_form_id,
        ticket_field_def_id=ticket_field_def_id,
        limit=limit,
        offset=offset,
    )
    items: List[TicketFormFieldOut] = [
        TicketFormFieldOut.model_validate(f, from_attributes=True) for f in fields
    ]
    return PaginationEnvelope[TicketFormFieldOut](
        items=items, total=total, limit=limit, offset=offset
    )


@router.post("/", response_model=TicketFormFieldOut, status_code=status.HTTP_201_CREATED)
def create_ticket_form_field_endpoint(
    tenant_id: UUID,
    form_field_in: TenantCreateTicketFormField,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFormFieldOut:
    """Create a new ticket form field for a tenant.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` on the association is set to
    ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    form_field = service_create_ticket_form_field(
        db,
        tenant_id=tenant_id,
        request=form_field_in,
        created_by=created_user,
    )
    return TicketFormFieldOut.model_validate(form_field, from_attributes=True)


@router.patch("/{form_field_id}", response_model=TicketFormFieldOut)
def update_ticket_form_field_endpoint(
    tenant_id: UUID,
    form_field_id: UUID,
    form_field_update: TicketFormFieldUpdate,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> TicketFormFieldOut:
    """Update an existing ticket form field.

    Only the display order can be updated.  The ``X-User`` header
    supplies the identity of the caller for audit purposes.
    """
    updated_user = x_user or "anonymous"
    form_field = service_update_ticket_form_field(
        db,
        tenant_id=tenant_id,
        form_field_id=form_field_id,
        request=form_field_update,
        updated_by=updated_user,
    )
    return TicketFormFieldOut.model_validate(form_field, from_attributes=True)


@router.get("/{form_field_id}", response_model=TicketFormFieldOut)
def get_ticket_form_field_endpoint(
    tenant_id: UUID,
    form_field_id: UUID,
    db: Session = Depends(get_db),
) -> TicketFormFieldOut:
    """Retrieve a single ticket form field by ID within a tenant.

    Raises 404 if the association does not exist or does not belong to
    the tenant.
    """
    form_field = service_get_ticket_form_field(
        db, tenant_id=tenant_id, form_field_id=form_field_id
    )
    return TicketFormFieldOut.model_validate(form_field, from_attributes=True)


@router.delete("/{form_field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_form_field_endpoint(
    tenant_id: UUID,
    form_field_id: UUID,
    db: Session = Depends(get_db),
    x_user: str | None = Query(default=None),
) -> None:
    """Delete a ticket form field from a tenant.

    Returns HTTP 204 on success.  Raises 404 if the association does
    not exist or does not belong to the tenant.  The ``X-User``
    header is currently ignored for deletion events; event publishers
    do not include user information for deletions.
    """
    service_delete_ticket_form_field(
        db, tenant_id=tenant_id, form_field_id=form_field_id
    )
    return None
