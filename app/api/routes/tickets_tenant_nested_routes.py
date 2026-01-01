"""
Tenant‑scoped nested resource endpoints for tickets.

This router exposes CRUD operations on nested ticket resources such as
participants and tags.  All endpoints enforce tenant scoping and
delegate to the appropriate service layer functions.  Participants
and tags are append‑only; only creation and deletion are supported.

Endpoint patterns:

* ``GET /tenants/{tenant_id}/tickets/{ticket_id}/participants`` –
  List participants on a ticket.
* ``POST /tenants/{tenant_id}/tickets/{ticket_id}/participants`` –
  Add a participant to a ticket.
* ``DELETE /tenants/{tenant_id}/tickets/{ticket_id}/participants/{participant_id}`` –
  Remove a participant from a ticket.
* ``GET /tenants/{tenant_id}/tickets/{ticket_id}/tags`` –
  List tags on a ticket.
* ``POST /tenants/{tenant_id}/tickets/{ticket_id}/tags`` –
  Add a tag to a ticket.
* ``DELETE /tenants/{tenant_id}/tickets/{ticket_id}/tags/{tag_id}`` –
  Remove a tag from a ticket.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status, HTTPException
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
    TenantCreateTicketParticipant,
    TicketParticipantOut,
)
from app.domain.schemas.ticket_tag import (
    TenantCreateTicketTag,
    TicketTagOut,
)

from app.domain.schemas.ticket_message import (
    TenantCreateTicketMessage,
    TicketMessageOut,
)

from app.domain.schemas.ticket_attachment import (
    TenantCreateTicketAttachment,
    TicketAttachmentOut,
)
from app.domain.schemas.ticket_field_value import (
    TenantCreateTicketFieldValue,
    TicketFieldValueUpdate,
    TicketFieldValueOut,
)

from app.domain.schemas.ticket_assignment import (
    TenantCreateTicketAssignment,
    TicketAssignmentOut,
)
from app.domain.schemas.ticket_audit import TicketAuditOut
from app.domain.schemas.ticket_task_mirror import TicketTaskMirrorOut
from app.domain.schemas.ticket_ai_work_ref import TicketAiWorkRefOut

# Import time entry and CSAT response schemas
from app.domain.schemas.ticket_time_entry import (
    TenantCreateTicketTimeEntry,
    TicketTimeEntryUpdate,
    TicketTimeEntryOut,
)
from app.domain.schemas.csat_response import (
    TenantCreateCsatResponse,
    CsatResponseOut,
)

# Import reporting primitives schemas
from app.domain.schemas.ticket_metrics import TicketMetricsOut
from app.domain.schemas.ticket_status_duration import TicketStatusDurationOut

from app.domain.services import (
    ticket_time_entry_service,
    csat_response_service,
    ticket_metrics_service,
    ticket_status_duration_service,
)


router = APIRouter(
    prefix="/tenants/{tenant_id}/tickets/{ticket_id}",
    tags=["Ticket Nested Resources"],
)


# ---------------------------------------------------------------------------
# Participant endpoints
# ---------------------------------------------------------------------------


@router.get("/participants", response_model=List[TicketParticipantOut])
def list_ticket_participants_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    participant_type: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketParticipantOut]:
    """List participants for a ticket within a tenant."""
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
def create_ticket_participant_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    participant_in: TenantCreateTicketParticipant,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketParticipantOut:
    """Add a participant to a ticket."""
    created_by = x_user or "anonymous"
    participant = ticket_participant_service.create_ticket_participant(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=participant_in,
        created_by=created_by,
    )
    return TicketParticipantOut.model_validate(participant, from_attributes=True)


@router.delete(
    "/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_participant_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    participant_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a participant from a ticket."""
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
def list_ticket_tags_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    db: Session = Depends(get_db),
) -> List[TicketTagOut]:
    """List tags for a ticket within a tenant."""
    tags = ticket_tag_service.list_ticket_tags(
        db, tenant_id=tenant_id, ticket_id=ticket_id
    )
    return [TicketTagOut.model_validate(t, from_attributes=True) for t in tags]


@router.post(
    "/tags",
    response_model=TicketTagOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_tag_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    tag_in: TenantCreateTicketTag,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketTagOut:
    """Add a tag to a ticket."""
    created_by = x_user or "anonymous"
    tag = ticket_tag_service.create_ticket_tag(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=tag_in,
        created_by=created_by,
    )
    return TicketTagOut.model_validate(tag, from_attributes=True)


@router.delete(
    "/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_tag_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    tag_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a tag from a ticket."""
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
def list_ticket_messages_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    author_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    channel_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketMessageOut]:
    """List messages for a ticket within a tenant."""
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
def create_ticket_message_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    message_in: TenantCreateTicketMessage,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketMessageOut:
    """Add a message to a ticket."""
    created_by = x_user or "anonymous"
    message = ticket_message_service.create_ticket_message(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=message_in,
        created_by=created_by,
    )
    return TicketMessageOut.model_validate(message, from_attributes=True)


# ---------------------------------------------------------------------------
# Attachment endpoints
# ---------------------------------------------------------------------------


@router.get("/attachments", response_model=List[TicketAttachmentOut])
def list_ticket_attachments_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    ticket_message_id: Optional[UUID] = None,
    storage_provider: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketAttachmentOut]:
    """List attachments for a ticket within a tenant."""
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
def create_ticket_attachment_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    attachment_in: TenantCreateTicketAttachment,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketAttachmentOut:
    """Add an attachment to a ticket."""
    created_by = x_user or "anonymous"
    attachment = ticket_attachment_service.create_ticket_attachment(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=attachment_in,
        created_by=created_by,
    )
    return TicketAttachmentOut.model_validate(attachment, from_attributes=True)


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_attachment_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    attachment_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove an attachment from a ticket."""
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
def list_ticket_assignments_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    db: Session = Depends(get_db),
) -> List[TicketAssignmentOut]:
    """List assignment history for a ticket within a tenant."""
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
def create_ticket_assignment_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    assignment_in: TenantCreateTicketAssignment,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketAssignmentOut:
    """Create a ticket assignment within a tenant."""
    created_by = x_user or "anonymous"
    assignment = ticket_assignment_service.create_ticket_assignment(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=assignment_in,
        created_by=created_by,
    )
    return TicketAssignmentOut.model_validate(assignment, from_attributes=True)


# ---------------------------------------------------------------------------
# Audit endpoints (read-only)
# ---------------------------------------------------------------------------


@router.get("/audits", response_model=List[TicketAuditOut])
def list_ticket_audits_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    event_type: Optional[str] = None,
    actor_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TicketAuditOut]:
    """List audit events for a ticket within a tenant."""
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
def list_ticket_field_values_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    ticket_field_def_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketFieldValueOut]:
    """List custom field values for a ticket within a tenant.

    Optional filtering by the field definition is supported.  Results
    are ordered by creation time ascending.  Pagination can be
    controlled via ``limit`` and ``offset``.
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
def create_ticket_field_value_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    value_in: TenantCreateTicketFieldValue,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketFieldValueOut:
    """Add a custom field value to a ticket.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  If omitted, ``created_by`` and ``updated_by`` on the
    value are set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    value = ticket_field_value_service.create_ticket_field_value(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=value_in,
        created_by=created_user,
    )
    return TicketFieldValueOut.model_validate(value, from_attributes=True)


@router.get(
    "/field_values/{value_id}",
    response_model=TicketFieldValueOut,
)
def get_ticket_field_value_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    value_id: UUID,
    db: Session = Depends(get_db),
) -> TicketFieldValueOut:
    """Retrieve a single custom field value by ID within a tenant and ticket."""
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
def update_ticket_field_value_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    value_id: UUID,
    value_update: TicketFieldValueUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketFieldValueOut:
    """Update an existing custom field value on a ticket.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes.  Fields not provided in the request are left unchanged.
    """
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


# ---------------------------------------------------------------------------
# Task mirror endpoints (read-only for tenants)
# ---------------------------------------------------------------------------


@router.get(
    "/task_mirrors",
    response_model=List[TicketTaskMirrorOut],
)
def list_ticket_task_mirrors_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketTaskMirrorOut]:
    """List mirrored tasks for a ticket within a tenant.

    Results can be filtered by task status and paginated via ``limit`` and
    ``offset``.
    """
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
def get_ticket_task_mirror_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    mirror_id: UUID,
    db: Session = Depends(get_db),
) -> TicketTaskMirrorOut:
    """Retrieve a single task mirror by ID for a ticket within a tenant."""
    mirror = ticket_task_mirror_service.get_ticket_task_mirror(
        db,
        tenant_id=tenant_id,
        mirror_id=mirror_id,
    )
    # Validate ticket_id matches requested ticket
    if mirror.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket task mirror not found for this ticket",
        )
    return TicketTaskMirrorOut.model_validate(mirror, from_attributes=True)


# ---------------------------------------------------------------------------
# AI work reference endpoints (read-only for tenants)
# ---------------------------------------------------------------------------


@router.get(
    "/ai_work_refs",
    response_model=List[TicketAiWorkRefOut],
)
def list_ticket_ai_work_refs_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    agent_key: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketAiWorkRefOut]:
    """List AI work references for a ticket within a tenant.

    Results can be filtered by agent key and paginated via ``limit`` and
    ``offset``.
    """
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
def get_ticket_ai_work_ref_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    ref_id: UUID,
    db: Session = Depends(get_db),
) -> TicketAiWorkRefOut:
    """Retrieve a single AI work reference by ID for a ticket within a tenant."""
    ref = ticket_ai_work_ref_service.get_ticket_ai_work_ref(
        db,
        tenant_id=tenant_id,
        ref_id=ref_id,
    )
    # Validate ticket_id matches
    if ref.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI work reference not found for this ticket",
        )
    return TicketAiWorkRefOut.model_validate(ref, from_attributes=True)


# ---------------------------------------------------------------------------
# Time entry endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/time_entries",
    response_model=List[TicketTimeEntryOut],
)
def list_ticket_time_entries_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    user_id: Optional[UUID] = None,
    work_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketTimeEntryOut]:
    """List time entries for a ticket within a tenant.

    Results can be filtered by the user who logged the time and the work
    type. Pagination is supported via ``limit`` and ``offset``.
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
def create_ticket_time_entry_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    time_entry_in: TenantCreateTicketTimeEntry,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketTimeEntryOut:
    """Add a time entry to a ticket.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes. If omitted, ``created_by`` is set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    entry = ticket_time_entry_service.create_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=time_entry_in,
        created_by=created_user,
    )
    return TicketTimeEntryOut.model_validate(entry, from_attributes=True)


@router.get(
    "/time_entries/{entry_id}",
    response_model=TicketTimeEntryOut,
)
def get_ticket_time_entry_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    entry_id: UUID,
    db: Session = Depends(get_db),
) -> TicketTimeEntryOut:
    """Retrieve a single time entry by ID within a tenant and ticket."""
    entry = ticket_time_entry_service.get_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        time_entry_id=entry_id,
    )
    # Validate ticket_id matches
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
def update_ticket_time_entry_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    entry_id: UUID,
    time_entry_update: TicketTimeEntryUpdate,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> TicketTimeEntryOut:
    """Update an existing time entry on a ticket.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes. Only fields provided in the request will be updated.
    """
    updated_user = x_user or "anonymous"
    entry = ticket_time_entry_service.update_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        time_entry_id=entry_id,
        request=time_entry_update,
        updated_by=updated_user,
    )
    # Validate ticket_id matches
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
def delete_ticket_time_entry_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    entry_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a time entry from a ticket."""
    # Validate existence and ticket match inside service
    ticket_time_entry_service.delete_ticket_time_entry(
        db,
        tenant_id=tenant_id,
        time_entry_id=entry_id,
    )
    return None


# ---------------------------------------------------------------------------
# CSAT response endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/csat_responses",
    response_model=List[CsatResponseOut],
)
def list_csat_responses_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    csat_survey_id: Optional[UUID] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[CsatResponseOut]:
    """List CSAT responses for a ticket within a tenant.

    Results can be filtered by survey and paginated via ``limit`` and
    ``offset``. Responses are returned in chronological order of submission.
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
def create_csat_response_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    response_in: TenantCreateCsatResponse,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> CsatResponseOut:
    """Submit a new CSAT response for a ticket.

    The ``X-User`` header supplies the identity of the caller for audit
    purposes. If omitted, ``created_by`` is set to ``"anonymous"``.
    """
    created_user = x_user or "anonymous"
    resp = csat_response_service.create_csat_response(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        request=response_in,
        created_by=created_user,
    )
    return CsatResponseOut.model_validate(resp, from_attributes=True)


@router.get(
    "/csat_responses/{response_id}",
    response_model=CsatResponseOut,
)
def get_csat_response_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    response_id: UUID,
    db: Session = Depends(get_db),
) -> CsatResponseOut:
    """Retrieve a single CSAT response by ID within a tenant and ticket."""
    resp = csat_response_service.get_csat_response(
        db,
        tenant_id=tenant_id,
        response_id=response_id,
    )
    # Validate ticket_id matches
    if resp.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSAT response not found for this ticket",
        )
    return CsatResponseOut.model_validate(resp, from_attributes=True)


# ---------------------------------------------------------------------------
# Ticket metrics endpoints (read‑only for tenants)
# ---------------------------------------------------------------------------


@router.get(
    "/metrics",
    response_model=List[TicketMetricsOut],
)
def list_ticket_metrics_tenant_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketMetricsOut]:
    """List ticket metrics for a ticket within a tenant.

    Returns a list of metrics records (typically zero or one) for the
    specified ticket. Pagination is supported via ``limit`` and
    ``offset``, though metrics are unique per ticket.
    """
    metrics_list, _ = ticket_metrics_service.list_ticket_metrics(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        limit=limit,
        offset=offset,
    )
    return [TicketMetricsOut.model_validate(m, from_attributes=True) for m in metrics_list]


@router.get(
    "/metrics/{metrics_id}",
    response_model=TicketMetricsOut,
)
def get_ticket_metrics_tenant_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    metrics_id: UUID,
    db: Session = Depends(get_db),
) -> TicketMetricsOut:
    """Retrieve a single ticket metrics record by ID within a tenant and ticket."""
    metrics = ticket_metrics_service.get_ticket_metrics(
        db,
        tenant_id=tenant_id,
        metrics_id=metrics_id,
    )
    # Validate ticket_id matches
    if metrics.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket metrics not found for this ticket",
        )
    return TicketMetricsOut.model_validate(metrics, from_attributes=True)


# ---------------------------------------------------------------------------
# Ticket status duration endpoints (read‑only for tenants)
# ---------------------------------------------------------------------------


@router.get(
    "/status_durations",
    response_model=List[TicketStatusDurationOut],
)
def list_ticket_status_durations_tenant_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[TicketStatusDurationOut]:
    """List status duration records for a ticket within a tenant.

    Results can be filtered by status and paginated via ``limit`` and
    ``offset``.  Records are returned in chronological order of
    ``started_at``.
    """
    durations, _ = ticket_status_duration_service.list_ticket_status_durations(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        TicketStatusDurationOut.model_validate(d, from_attributes=True)
        for d in durations
    ]


@router.get(
    "/status_durations/{duration_id}",
    response_model=TicketStatusDurationOut,
)
def get_ticket_status_duration_tenant_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    duration_id: UUID,
    db: Session = Depends(get_db),
) -> TicketStatusDurationOut:
    """Retrieve a single status duration record by ID within a tenant and ticket."""
    duration = ticket_status_duration_service.get_ticket_status_duration(
        db,
        tenant_id=tenant_id,
        duration_id=duration_id,
    )
    # Validate ticket_id matches
    if duration.ticket_id != ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket status duration not found for this ticket",
        )
    return TicketStatusDurationOut.model_validate(duration, from_attributes=True)


@router.delete(
    "/field_values/{value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_field_value_endpoint(
    tenant_id: UUID,
    ticket_id: UUID,
    value_id: UUID,
    db: Session = Depends(get_db),
    x_user: Optional[str] = Header(None, alias="X-User"),
) -> None:
    """Remove a custom field value from a ticket."""
    ticket_field_value_service.delete_ticket_field_value(
        db,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        value_id=value_id,
    )
    return None