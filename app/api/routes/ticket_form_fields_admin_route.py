"""
Admin‑scoped FastAPI routes for ticket form fields.

These endpoints allow administrators to manage associations between
ticket forms and custom field definitions across tenants.  All
operations require a ``tenant_id`` parameter to ensure proper
scoping, except for creation where the tenant ID is part of the
request body.  Only the display order can be updated after
creation.  Audit fields are populated from the ``X-User`` header
when provided; otherwise "anonymous" is used.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
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
    AdminCreateTicketFormField,
    TicketFormFieldUpdate,
    TicketFormFieldOut,
)
from app.domain.schemas.common import PaginationEnvelope


router = APIRouter(
    prefix="/admin/ticket_form_fields",
    tags=["TicketFormFields"],
)


@router.get("/", response_model=PaginationEnvelope[TicketFormFieldOut])
def list_ticket_form_fields_admin_endpoint(
    *,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form fields to scope the search"
    ),
    ticket_form_id: Optional[UUID] = None,
    ticket_field_def_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> PaginationEnvelope[TicketFormFieldOut]:
    """List ticket form fields in an admin context with optional filters.

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
def create_ticket_form_field_admin_endpoint(
    *,
    form_field_in: AdminCreateTicketFormField,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketFormFieldOut:
    """Create a new ticket form field via the admin API.

    The ``AdminCreateTicketFormField`` request must include ``tenant_id``.
    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` on the association is set to
    ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    form_field = service_create_ticket_form_field(
        db,
        tenant_id=form_field_in.tenant_id,
        request=form_field_in,
        created_by=created_user,
    )
    return TicketFormFieldOut.model_validate(form_field, from_attributes=True)


@router.patch("/{form_field_id}", response_model=TicketFormFieldOut)
def update_ticket_form_field_admin_endpoint(
    *,
    form_field_id: UUID,
    form_field_update: TicketFormFieldUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form field to update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketFormFieldOut:
    """Update an existing ticket form field via the admin API.

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
def get_ticket_form_field_admin_endpoint(
    *,
    form_field_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form field to retrieve"
    ),
    db: Session = Depends(get_db),
) -> TicketFormFieldOut:
    """Retrieve a single ticket form field by ID via the admin API.

    Raises 404 if the association does not exist or does not belong to
    the specified tenant.
    """
    form_field = service_get_ticket_form_field(
        db, tenant_id=tenant_id, form_field_id=form_field_id
    )
    return TicketFormFieldOut.model_validate(form_field, from_attributes=True)


@router.delete("/{form_field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_form_field_admin_endpoint(
    *,
    form_field_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket form field to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Delete a ticket form field via the admin API.

    Returns HTTP 204 on success.  Raises 404 if the association does
    not exist or does not belong to the specified tenant.  The
    ``X-User`` header is currently ignored for deletion events; event
    publishers do not include user information for deletions.
    """
    service_delete_ticket_form_field(
        db, tenant_id=tenant_id, form_field_id=form_field_id
    )
    return None
