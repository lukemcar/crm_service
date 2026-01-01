"""
Admin‑scoped nested resource endpoints for tickets.

This router exposes CRUD operations on nested ticket resources such as
participants and tags in an admin context.  All endpoints require
specifying the tenant_id via query parameters to ensure that the
operation is scoped correctly.  Participants and tags are
append‑only; only creation and deletion are supported.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.services import (
    ticket_participant_service,
    ticket_tag_service,
    ticket_message_service,
    ticket_attachment_service,
    ticket_assignment_service,
    ticket_audit_service,
    ticket_field_value_service,
    ticket_task_mirror_service,
    ticket_ai_work_ref_service,
)
from app.domain.schemas.ticket_participant import (
    AdminCreateTicketParticipant,
    TicketParticipantOut,
)
from app.domain.schemas.ticket_tag import (
    AdminCreateTicketTag,
    TicketTagOut,
)

from app.domain.schemas.ticket_message import (
    AdminCreateTicketMessage,
    TicketMessageOut,
)

from app.domain.schemas.ticket_attachment import (
    AdminCreateTicketAttachment,
    TicketAttachmentOut,
)
from app.domain.schemas.ticket_field_value import (
    AdminCreateTicketFieldValue,
    TicketFieldValueUpdate,
    TicketFieldValueOut,
)

from app.domain.schemas.ticket_assignment import (
    AdminCreateTicketAssignment,
    TicketAssignmentOut,
)
from app.domain.schemas.ticket_audit import TicketAuditOut
from app.domain.schemas.ticket_task_mirror import TicketTaskMirrorOut
from app.domain.schemas.ticket_ai_work_ref import TicketAiWorkRefOut

# Import time entry and CSAT response schemas for admin context
from app.domain.schemas.ticket_time_entry import (
    AdminCreateTicketTimeEntry,
    TicketTimeEntryUpdate,
    TicketTimeEntryOut,
)
from app.domain.schemas.csat_response import (
    AdminCreateCsatResponse,
    CsatResponseUpdate,
    CsatResponseOut,
)

from app.domain.services import ticket_time_entry_service, csat_response_service

# Import reporting primitives schemas and services
from app.domain.schemas.ticket_metrics import (
    AdminCreateTicketMetrics,
    TicketMetricsUpdate,
    TicketMetricsOut,
)
from app.domain.schemas.ticket_status_duration import (
    AdminCreateTicketStatusDuration,
    AdminUpdateTicketStatusDuration,
    TicketStatusDurationOut,
)

from app.domain.services import ticket_metrics_service, ticket_status_duration_service


router = APIRouter(
    prefix="/admin/tickets/{ticket_id}",
    tags=["Ticket Nested Resources"],
)


# ---------------------------------------------------------------------------
# Participant endpoints
# ---------------------------------------------------------------------------


@router.get("/participants", response_model=List[TicketParticipantOut])
def list_ticket_participants_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    participant_type: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketParticipantOut]:
    """List participants on a ticket in an admin context."""
    participants = ticket_participant_service.list_ticket_participants(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_type=participant_type,
        role=role,
    )
    return [TicketParticipantOut.model_validate(p, from_attributes=True) for p in participants]


@router.post(
    "/participants",
    response_model=TicketParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_participant_admin_endpoint(
    *,
    ticket_id: UUID,
    participant_in: AdminCreateTicketParticipant,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketParticipantOut:
    """Add a participant to a ticket via the admin API."""
    created_by = x_user or "anonymous"
    participant = ticket_participant_service.create_ticket_participant(
        db,
        tenant_id=participant_in.tenant_id,
        ticket_id=ticket_id,
        request=participant_in,
        created_by=created_by,
    )
    return TicketParticipantOut.model_validate(participant, from_attributes=True)


@router.delete(
    "/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_participant_admin_endpoint(
    *,
    ticket_id: UUID,
    participant_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket participant to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a participant from a ticket via the admin API."""
    ticket_participant_service.delete_ticket_participant(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        participant_id=participant_id,
    )
    return None


# ---------------------------------------------------------------------------
# Tag endpoints
# ---------------------------------------------------------------------------


@router.get("/tags", response_model=List[TicketTagOut])
def list_ticket_tags_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> List[TicketTagOut]:
    """List tags on a ticket in an admin context."""
    tags = ticket_tag_service.list_ticket_tags(
        db, tenant_id=tenant_id, ticket_id=ticket_id
    )
    return [TicketTagOut.model_validate(t, from_attributes=True) for t in tags]


@router.post(
    "/tags",
    response_model=TicketTagOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_tag_admin_endpoint(
    *,
    ticket_id: UUID,
    tag_in: AdminCreateTicketTag,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketTagOut:
    """Add a tag to a ticket via the admin API."""
    created_by = x_user or "anonymous"
    tag = ticket_tag_service.create_ticket_tag(
        db,
        tenant_id=tag_in.tenant_id,
        ticket_id=ticket_id,
        request=tag_in,
        created_by=created_by,
    )
    return TicketTagOut.model_validate(tag, from_attributes=True)


@router.delete(
    "/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_tag_admin_endpoint(
    *,
    ticket_id: UUID,
    tag_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket tag to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a tag from a ticket via the admin API."""
    ticket_tag_service.delete_ticket_tag(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        tag_id=tag_id,
    )
    return None


# ---------------------------------------------------------------------------
# Message endpoints
# ---------------------------------------------------------------------------


@router.get("/messages", response_model=List[TicketMessageOut])
def list_ticket_messages_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    author_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    channel_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketMessageOut]:
    """List messages on a ticket in an admin context."""
    messages = ticket_message_service.list_ticket_messages(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        author_type=author_type,
        is_public=is_public,
        channel_type=channel_type,
    )
    return [TicketMessageOut.model_validate(m, from_attributes=True) for m in messages]


@router.post(
    "/messages",
    response_model=TicketMessageOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_message_admin_endpoint(
    *,
    ticket_id: UUID,
    message_in: AdminCreateTicketMessage,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketMessageOut:
    """Add a message to a ticket via the admin API."""
    created_by = x_user or "anonymous"
    message = ticket_message_service.create_ticket_message(
        db,
        tenant_id=message_in.tenant_id,
        ticket_id=ticket_id,
        request=message_in,
        created_by=created_by,
    )
    return TicketMessageOut.model_validate(message, from_attributes=True)


# ---------------------------------------------------------------------------
# Attachment endpoints
# ---------------------------------------------------------------------------


@router.get("/attachments", response_model=List[TicketAttachmentOut])
def list_ticket_attachments_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    ticket_message_id: Optional[UUID] = None,
    storage_provider: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketAttachmentOut]:
    """List attachments on a ticket in an admin context."""
    attachments = ticket_attachment_service.list_ticket_attachments(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_message_id=ticket_message_id,
        storage_provider=storage_provider,
    )
    return [TicketAttachmentOut.model_validate(a, from_attributes=True) for a in attachments]


@router.post(
    "/attachments",
    response_model=TicketAttachmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_attachment_admin_endpoint(
    *,
    ticket_id: UUID,
    attachment_in: AdminCreateTicketAttachment,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketAttachmentOut:
    """Add an attachment to a ticket via the admin API."""
    created_by = x_user or "anonymous"
    attachment = ticket_attachment_service.create_ticket_attachment(
        db,
        tenant_id=attachment_in.tenant_id,
        ticket_id=ticket_id,
        request=attachment_in,
        created_by=created_by,
    )
    return TicketAttachmentOut.model_validate(attachment, from_attributes=True)


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_attachment_admin_endpoint(
    *,
    ticket_id: UUID,
    attachment_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket attachment to delete"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove an attachment from a ticket via the admin API."""
    ticket_attachment_service.delete_ticket_attachment(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        attachment_id=attachment_id,
    )
    return None


# ---------------------------------------------------------------------------
# Assignment endpoints
# ---------------------------------------------------------------------------


@router.get("/assignments", response_model=List[TicketAssignmentOut])
def list_ticket_assignments_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> List[TicketAssignmentOut]:
    """List assignment history on a ticket in an admin context."""
    assignments = ticket_assignment_service.list_ticket_assignments(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
    )
    return [TicketAssignmentOut.model_validate(a, from_attributes=True) for a in assignments]


@router.post(
    "/assignments",
    response_model=TicketAssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_assignment_admin_endpoint(
    *,
    ticket_id: UUID,
    assignment_in: AdminCreateTicketAssignment,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketAssignmentOut:
    """Create a ticket assignment via the admin API."""
    created_by = x_user or "anonymous"
    assignment = ticket_assignment_service.create_ticket_assignment(
        db,
        tenant_id=assignment_in.tenant_id,
        ticket_id=ticket_id,
        request=assignment_in,
        created_by=created_by,
    )
    return TicketAssignmentOut.model_validate(assignment, from_attributes=True)


# ---------------------------------------------------------------------------
# Audit endpoints (read-only)
# ---------------------------------------------------------------------------


@router.get("/audits", response_model=List[TicketAuditOut])
def list_ticket_audits_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    event_type: Optional[str] = None,
    actor_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketAuditOut]:
    """List audit events on a ticket in an admin context."""
    audits = ticket_audit_service.list_ticket_audits(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        event_type=event_type,
        actor_type=actor_type,
    )
    return [TicketAuditOut.model_validate(a, from_attributes=True) for a in audits]


# ---------------------------------------------------------------------------
# Field value endpoints
# ---------------------------------------------------------------------------


@router.get("/field_values", response_model=List[TicketFieldValueOut])
def list_ticket_field_values_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    ticket_field_def_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketFieldValueOut]:
    """List custom field values on a ticket in an admin context.

    Optional filtering by the field definition is supported.  Results are
    ordered by creation time ascending.  Pagination can be controlled via
    ``limit`` and ``offset``.
    """
    values, _ = ticket_field_value_service.list_ticket_field_values(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        ticket_field_def_id=ticket_field_def_id,
        limit=limit,
        offset=offset,
    )
    return [TicketFieldValueOut.model_validate(v, from_attributes=True) for v in values]


@router.post(
    "/field_values",
    response_model=TicketFieldValueOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_field_value_admin_endpoint(
    *,
    ticket_id: UUID,
    value_in: AdminCreateTicketFieldValue,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketFieldValueOut:
    """Add a custom field value to a ticket via the admin API.

    The ``AdminCreateTicketFieldValue`` request must include ``tenant_id``.
    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` on the
    value are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    value = ticket_field_value_service.create_ticket_field_value(
        db,
        tenant_id=value_in.tenant_id,
        ticket_id=ticket_id,
        request=value_in,
        created_by=created_user,
    )
    return TicketFieldValueOut.model_validate(value, from_attributes=True)


@router.get(
    "/field_values/{value_id}",
    response_model=TicketFieldValueOut,
)
def get_ticket_field_value_admin_endpoint(
    *,
    ticket_id: UUID,
    value_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> TicketFieldValueOut:
    """Retrieve a single custom field value via the admin API."""
    value = ticket_field_value_service.get_ticket_field_value(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
    )
    return TicketFieldValueOut.model_validate(value, from_attributes=True)


@router.patch(
    "/field_values/{value_id}",
    response_model=TicketFieldValueOut,
)
def update_ticket_field_value_admin_endpoint(
    *,
    ticket_id: UUID,
    value_id: UUID,
    value_update: TicketFieldValueUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketFieldValueOut:
    """Update an existing custom field value via the admin API."""
    updated_user = x_user or "anonymous"
    value = ticket_field_value_service.update_ticket_field_value(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
        request=value_update,
        updated_by=updated_user,
    )
    return TicketFieldValueOut.model_validate(value, from_attributes=True)


@router.delete(
    "/field_values/{value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_field_value_admin_endpoint(
    *,
    ticket_id: UUID,
    value_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a custom field value from a ticket via the admin API."""
    ticket_field_value_service.delete_ticket_field_value(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
    )
    return None


# ---------------------------------------------------------------------------
# Task mirror endpoints (read-only for admin per ticket)
# ---------------------------------------------------------------------------


@router.get(
    "/task_mirrors",
    response_model=List[TicketTaskMirrorOut],
)
def list_ticket_task_mirrors_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketTaskMirrorOut]:
    """List mirrored tasks on a ticket in an admin context."""
    tasks, _ = ticket_task_mirror_service.list_ticket_task_mirrors(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [TicketTaskMirrorOut.model_validate(t, from_attributes=True) for t in tasks]


@router.get(
    "/task_mirrors/{mirror_id}",
    response_model=TicketTaskMirrorOut,
)
def get_ticket_task_mirror_admin_endpoint(
    *,
    ticket_id: UUID,
    mirror_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> TicketTaskMirrorOut:
    """Retrieve a single mirrored task via the admin API."""
    mirror = ticket_task_mirror_service.get_ticket_task_mirror(
        db,
        tenant_id=tenant_id,
        mirror_id=mirror_id,
    )
    # Validate ticket_id matches
    if mirror.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket task mirror not found for this ticket",
        )
    return TicketTaskMirrorOut.model_validate(mirror, from_attributes=True)


# ---------------------------------------------------------------------------
# AI work reference endpoints (read-only for admin per ticket)
# ---------------------------------------------------------------------------


@router.get(
    "/ai_work_refs",
    response_model=List[TicketAiWorkRefOut],
)
def list_ticket_ai_work_refs_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    agent_key: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketAiWorkRefOut]:
    """List AI work references on a ticket in an admin context."""
    refs, _ = ticket_ai_work_ref_service.list_ticket_ai_work_refs(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        agent_key=agent_key,
        limit=limit,
        offset=offset,
    )
    return [TicketAiWorkRefOut.model_validate(r, from_attributes=True) for r in refs]


@router.get(
    "/ai_work_refs/{ref_id}",
    response_model=TicketAiWorkRefOut,
)
def get_ticket_ai_work_ref_admin_endpoint(
    *,
    ticket_id: UUID,
    ref_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> TicketAiWorkRefOut:
    """Retrieve a single AI work reference via the admin API."""
    ref = ticket_ai_work_ref_service.get_ticket_ai_work_ref(
        db,
        tenant_id=tenant_id,
        ref_id=ref_id,
    )
    if ref.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket AI work reference not found for this ticket",
        )
    return TicketAiWorkRefOut.model_validate(ref, from_attributes=True)


# ---------------------------------------------------------------------------
# Time entry endpoints (admin context)
# ---------------------------------------------------------------------------


@router.get(
    "/time_entries",
    response_model=List[TicketTimeEntryOut],
)
def list_ticket_time_entries_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    user_id: Optional[UUID] = None,
    work_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketTimeEntryOut]:
    """List time entries on a ticket in an admin context.

    Results can be filtered by the user who logged the time and the work type.
    Pagination is supported via ``limit`` and ``offset``.
    """
    entries, _ = ticket_time_entry_service.list_ticket_time_entries(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        user_id=user_id,
        work_type=work_type,
        limit=limit,
        offset=offset,
    )
    return [TicketTimeEntryOut.model_validate(e, from_attributes=True) for e in entries]


@router.post(
    "/time_entries",
    response_model=TicketTimeEntryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_time_entry_admin_endpoint(
    *,
    ticket_id: UUID,
    time_entry_in: AdminCreateTicketTimeEntry,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketTimeEntryOut:
    """Add a time entry to a ticket via the admin API.

    The request must include ``tenant_id`` and ``ticket_id``; the path
    ticket_id must match the request ticket_id. The ``X-User`` header
    supplies the identity of the caller for audit purposes. If omitted,
    ``created_by`` is set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    if time_entry_in.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path ticket_id does not match request ticket_id",
        )
    entry = ticket_time_entry_service.create_ticket_time_entry(
        db,
        tenant_id=time_entry_in.tenant_id,
        ticket_id=ticket_id,
        request=time_entry_in,
        created_by=created_user,
    )
    return TicketTimeEntryOut.model_validate(entry, from_attributes=True)


@router.get(
    "/time_entries/{entry_id}",
    response_model=TicketTimeEntryOut,
)
def get_ticket_time_entry_admin_endpoint(
    *,
    ticket_id: UUID,
    entry_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> TicketTimeEntryOut:
    """Retrieve a single time entry via the admin API."""
    entry = ticket_time_entry_service.get_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        time_entry_id=entry_id,
    )
    if entry.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found for this ticket",
        )
    return TicketTimeEntryOut.model_validate(entry, from_attributes=True)


@router.put(
    "/time_entries/{entry_id}",
    response_model=TicketTimeEntryOut,
)
def update_ticket_time_entry_admin_endpoint(
    *,
    ticket_id: UUID,
    entry_id: UUID,
    time_entry_update: TicketTimeEntryUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketTimeEntryOut:
    """Update an existing time entry via the admin API."""
    updated_user = x_user or "anonymous"
    entry = ticket_time_entry_service.update_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        time_entry_id=entry_id,
        request=time_entry_update,
        updated_by=updated_user,
    )
    if entry.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found for this ticket",
        )
    return TicketTimeEntryOut.model_validate(entry, from_attributes=True)


@router.delete(
    "/time_entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_time_entry_admin_endpoint(
    *,
    ticket_id: UUID,
    entry_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a time entry via the admin API."""
    ticket_time_entry_service.delete_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        time_entry_id=entry_id,
    )
    return None


# ---------------------------------------------------------------------------
# CSAT response endpoints (admin context)
# ---------------------------------------------------------------------------


@router.get(
    "/csat_responses",
    response_model=List[CsatResponseOut],
)
def list_csat_responses_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    csat_survey_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[CsatResponseOut]:
    """List CSAT responses on a ticket in an admin context.

    Results can be filtered by survey and paginated.
    """
    responses, _ = csat_response_service.list_csat_responses(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        csat_survey_id=csat_survey_id,
        limit=limit,
        offset=offset,
    )
    return [CsatResponseOut.model_validate(r, from_attributes=True) for r in responses]


@router.post(
    "/csat_responses",
    response_model=CsatResponseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_csat_response_admin_endpoint(
    *,
    ticket_id: UUID,
    response_in: AdminCreateCsatResponse,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatResponseOut:
    """Submit a new CSAT response via the admin API.

    The request must include ``tenant_id`` and ``ticket_id``; the path
    ticket_id must match the request ticket_id. The ``X-User`` header
    supplies the identity of the caller for audit purposes. If omitted,
    ``created_by`` is set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    if response_in.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path ticket_id does not match request ticket_id",
        )
    resp = csat_response_service.create_csat_response(
        db,
        tenant_id=response_in.tenant_id,
        ticket_id=ticket_id,
        request=response_in,
        created_by=created_user,
    )
    return CsatResponseOut.model_validate(resp, from_attributes=True)


@router.get(
    "/csat_responses/{response_id}",
    response_model=CsatResponseOut,
)
def get_csat_response_admin_endpoint(
    *,
    ticket_id: UUID,
    response_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> CsatResponseOut:
    """Retrieve a single CSAT response via the admin API."""
    resp = csat_response_service.get_csat_response(
        db,
        tenant_id=tenant_id,
        response_id=response_id,
    )
    if resp.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSAT response not found for this ticket",
        )
    return CsatResponseOut.model_validate(resp, from_attributes=True)


@router.put(
    "/csat_responses/{response_id}",
    response_model=CsatResponseOut,
)
def update_csat_response_admin_endpoint(
    *,
    ticket_id: UUID,
    response_id: UUID,
    response_update: CsatResponseUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatResponseOut:
    """Update an existing CSAT response via the admin API."""
    updated_user = x_user or "anonymous"
    resp = csat_response_service.update_csat_response(
        db,
        tenant_id=tenant_id,
        response_id=response_id,
        request=response_update,
        updated_by=updated_user,
    )
    if resp.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSAT response not found for this ticket",
        )
    return CsatResponseOut.model_validate(resp, from_attributes=True)


@router.delete(
    "/csat_responses/{response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_csat_response_admin_endpoint(
    *,
    ticket_id: UUID,
    response_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a CSAT response via the admin API."""
    csat_response_service.delete_csat_response(
        db,
        tenant_id=tenant_id,
        response_id=response_id,
    )
    return None


# ---------------------------------------------------------------------------
# Ticket metrics endpoints (admin context)
# ---------------------------------------------------------------------------


@router.get(
    "/metrics",
    response_model=List[TicketMetricsOut],
)
def list_ticket_metrics_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketMetricsOut]:
    """List ticket metrics on a ticket via the admin API."""
    metrics_list, _ = ticket_metrics_service.list_ticket_metrics(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        limit=limit,
        offset=offset,
    )
    return [TicketMetricsOut.model_validate(m, from_attributes=True) for m in metrics_list]


@router.post(
    "/metrics",
    response_model=TicketMetricsOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_metrics_admin_endpoint(
    *,
    ticket_id: UUID,
    metrics_in: AdminCreateTicketMetrics,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketMetricsOut:
    """Create a ticket metrics record via the admin API.

    The request must include ``tenant_id`` and ``ticket_id``; the path
    ticket_id must match the request ticket_id.  The ``X-User`` header
    supplies the identity of the caller for audit purposes.  If
    omitted, ``updated_by`` is set to ``"anonymous"`` on the record.
    """
    created_user = x_user or "anonymous"
    if metrics_in.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path ticket_id does not match request ticket_id",
        )
    metrics = ticket_metrics_service.create_ticket_metrics(
        db,
        request=metrics_in,
        created_by=created_user,
    )
    return TicketMetricsOut.model_validate(metrics, from_attributes=True)


@router.get(
    "/metrics/{metrics_id}",
    response_model=TicketMetricsOut,
)
def get_ticket_metrics_admin_endpoint(
    *,
    ticket_id: UUID,
    metrics_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> TicketMetricsOut:
    """Retrieve a ticket metrics record via the admin API."""
    metrics = ticket_metrics_service.get_ticket_metrics(
        db,
        tenant_id=tenant_id,
        metrics_id=metrics_id,
    )
    if metrics.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket metrics not found for this ticket",
        )
    return TicketMetricsOut.model_validate(metrics, from_attributes=True)


@router.put(
    "/metrics/{metrics_id}",
    response_model=TicketMetricsOut,
)
def update_ticket_metrics_admin_endpoint(
    *,
    ticket_id: UUID,
    metrics_id: UUID,
    metrics_update: TicketMetricsUpdate,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketMetricsOut:
    """Update an existing ticket metrics record via the admin API."""
    updated_user = x_user or "anonymous"
    metrics = ticket_metrics_service.update_ticket_metrics(
        db,
        tenant_id=tenant_id,
        metrics_id=metrics_id,
        request=metrics_update,
        updated_by=updated_user,
    )
    if metrics.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket metrics not found for this ticket",
        )
    return TicketMetricsOut.model_validate(metrics, from_attributes=True)


@router.delete(
    "/metrics/{metrics_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_metrics_admin_endpoint(
    *,
    ticket_id: UUID,
    metrics_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a ticket metrics record via the admin API."""
    ticket_metrics_service.delete_ticket_metrics(
        db,
        tenant_id=tenant_id,
        metrics_id=metrics_id,
    )
    return None


# ---------------------------------------------------------------------------
# Ticket status duration endpoints (admin context)
# ---------------------------------------------------------------------------


@router.get(
    "/status_durations",
    response_model=List[TicketStatusDurationOut],
)
def list_ticket_status_durations_admin_endpoint(
    *,
    ticket_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketStatusDurationOut]:
    """List ticket status duration records on a ticket via the admin API."""
    durations, _ = ticket_status_duration_service.list_ticket_status_durations(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [TicketStatusDurationOut.model_validate(d, from_attributes=True) for d in durations]


@router.post(
    "/status_durations",
    response_model=TicketStatusDurationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_status_duration_admin_endpoint(
    *,
    ticket_id: UUID,
    duration_in: AdminCreateTicketStatusDuration,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketStatusDurationOut:
    """Create a ticket status duration record via the admin API."""
    created_user = x_user or "anonymous"
    if duration_in.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path ticket_id does not match request ticket_id",
        )
    duration = ticket_status_duration_service.create_ticket_status_duration(
        db,
        request=duration_in,
        created_by=created_user,
    )
    return TicketStatusDurationOut.model_validate(duration, from_attributes=True)


@router.get(
    "/status_durations/{duration_id}",
    response_model=TicketStatusDurationOut,
)
def get_ticket_status_duration_admin_endpoint(
    *,
    ticket_id: UUID,
    duration_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the search"
    ),
    db: Session = Depends(get_db),
) -> TicketStatusDurationOut:
    """Retrieve a ticket status duration record via the admin API."""
    duration = ticket_status_duration_service.get_ticket_status_duration(
        db,
        tenant_id=tenant_id,
        duration_id=duration_id,
    )
    if duration.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket status duration not found for this ticket",
        )
    return TicketStatusDurationOut.model_validate(duration, from_attributes=True)


@router.put(
    "/status_durations/{duration_id}",
    response_model=TicketStatusDurationOut,
)
def update_ticket_status_duration_admin_endpoint(
    *,
    ticket_id: UUID,
    duration_id: UUID,
    duration_update: AdminUpdateTicketStatusDuration,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the update"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketStatusDurationOut:
    """Update an existing ticket status duration record via the admin API."""
    updated_user = x_user or "anonymous"
    duration = ticket_status_duration_service.update_ticket_status_duration(
        db,
        tenant_id=tenant_id,
        duration_id=duration_id,
        request=duration_update,
        updated_by=updated_user,
    )
    if duration.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket status duration not found for this ticket",
        )
    return TicketStatusDurationOut.model_validate(duration, from_attributes=True)


@router.delete(
    "/status_durations/{duration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_status_duration_admin_endpoint(
    *,
    ticket_id: UUID,
    duration_id: UUID,
    tenant_id: UUID = Query(
        ..., description="Tenant ID of the ticket to scope the deletion"
    ),
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a ticket status duration record via the admin API."""
    ticket_status_duration_service.delete_ticket_status_duration(
        db,
        tenant_id=tenant_id,
        duration_id=duration_id,
    )
    return None