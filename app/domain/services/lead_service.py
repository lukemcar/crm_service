"""
Service layer for managing Lead entities.

This module provides CRUD operations for Lead objects and emits events
after each database mutation.  The service functions mirror the
patterns used in the existing group_service module.  Leads are scoped
to a tenant and support optional search across first_name, last_name,
email and phone number fields.  JSON Patch operations are applied to
both top‑level attributes and the nested ``lead_data`` JSONB column.
"""

from __future__ import annotations

import copy
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Import commit_or_raise for robust transaction handling
from .common_service import commit_or_raise

from app.domain.models import Lead
from app.messaging.producers import LeadMessageProducer as LeadProducer
from app.domain.schemas.lead import CreateLead, UpdateLead
from app.domain.schemas.json_patch import JsonPatchOperation, JsonPatchRequest

logger = logging.getLogger("lead_service")


def list_leads(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[Lead], int]:
    """Return a filtered and paginated list of leads.

    When ``tenant_id`` is provided, results are scoped to the tenant.  Filters
    on ``first_name`` and ``last_name`` perform case‑insensitive partial
    matches against the corresponding columns.  ``phone_number`` and ``email``
    search within the ``lead_data`` JSON for array items whose ``value``
    property contains the given substring (case insensitive).

    Parameters
    ----------
    db: Session
        Active SQLAlchemy session.
    tenant_id: UUID | None
        Tenant to scope results to (required for tenant routes).
    first_name: str | None
        Substring to match against the lead's first_name.
    last_name: str | None
        Substring to match against the lead's last_name.
    phone_number: str | None
        Substring to match against any phone number value in lead_data.
    email: str | None
        Substring to match against any email value in lead_data.
    limit: int | None
        Maximum number of items to return.
    offset: int | None
        Number of items to skip from the start of the result set.

    Returns
    -------
    list[Lead], int
        A tuple of the list of Lead ORM objects and the total number of
        matching records prior to pagination.
    """
    query = db.query(Lead)
    # Scope by tenant if provided
    if tenant_id is not None:
        query = query.filter(Lead.tenant_id == tenant_id)
    # Name filters (case insensitive)
    if first_name:
        query = query.filter(Lead.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Lead.last_name.ilike(f"%{last_name}%"))

    # Eagerly load all candidate leads and perform JSONB filtering in Python.
    # This approach simplifies JSON searching logic at the cost of in
    # memory filtering.  For high volume workloads consider moving
    # JSONB filters into the database using jsonb functions.
    leads: List[Lead] = query.order_by(Lead.created_at.desc()).all()

    def match_in_lead_data(lead: Lead, key: str, pattern: str) -> bool:
        """Case insensitive substring match for phone/email within lead_data."""
        data = lead.lead_data or {}
        items = data.get(key, [])
        pattern_lower = pattern.lower()
        for item in items:
            try:
                value = item.get("value", "")
                if value and pattern_lower in value.lower():
                    return True
            except AttributeError:
                # Malformed item; ignore
                continue
        return False

    # Apply phone/email filters in memory
    if phone_number:
        leads = [ld for ld in leads if match_in_lead_data(ld, "phone_numbers", phone_number)]
    if email:
        leads = [ld for ld in leads if match_in_lead_data(ld, "emails", email)]

    total = len(leads)
    # Apply pagination
    if offset:
        leads = leads[offset:]
    if limit is not None:
        leads = leads[:limit]
    return leads, total


def _lead_snapshot(lead: Lead) -> Dict[str, Any]:
    """Return a dict snapshot of the lead for event payloads."""
    return {
        "tenant_id": lead.tenant_id,
        "lead_id": lead.id,
        "first_name": lead.first_name,
        "middle_name": lead.middle_name,
        "last_name": lead.last_name,
        "source": lead.source,
        "lead_data": lead.lead_data,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
        "created_by": lead.created_by,
        "updated_by": lead.updated_by,
    }


def create_lead(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    lead_in: CreateLead,
    created_user: str,
) -> Lead:
    """Create a new lead within the specified tenant.

    Parameters
    ----------
    db: Session
        Active SQLAlchemy session.
    tenant_id: UUID
        Tenant identifier to associate with the new lead.
    lead_in: CreateLead
        Pydantic model containing the fields for the new lead.
    created_user: str
        Identifier of the user creating the lead (for auditing).

    Returns
    -------
    Lead
        The newly created lead ORM object.
    """
    # Build ORM instance
    lead = Lead(
        tenant_id=tenant_id,
        first_name=lead_in.first_name,
        middle_name=lead_in.middle_name,
        last_name=lead_in.last_name,
        source=lead_in.source,
        lead_data=lead_in.lead_data.model_dump() if getattr(lead_in, "lead_data", None) else None,
        created_by=created_user,
        updated_by=created_user,
    )
    db.add(lead)
    # Commit and refresh using centralized error handling
    commit_or_raise(db, refresh=lead, action="create_lead")
    logger.info("Created lead %s for tenant %s", lead.id, tenant_id)
    # Emit event after commit
    snapshot = _lead_snapshot(lead)
    try:
        LeadProducer.send_lead_created(tenant_id=tenant_id, payload=snapshot)
    except Exception:
        logger.exception(
            "Failed to publish lead.created event tenant_id=%s lead_id=%s",
            tenant_id,
            lead.id,
        )
    return lead


def get_lead(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
) -> Lead:
    """Fetch a lead by primary key within the specified tenant.

    Raises HTTP 404 if the lead does not exist or does not belong to the
    tenant.
    """
    lead: Optional[Lead] = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.tenant_id == tenant_id)
        .first()
    )
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return lead


def update_lead(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    lead_in: UpdateLead,
    modified_user: str,
) -> Lead:
    """Perform a full update (replace) of a lead.

    Only provided fields in the Pydantic model are used to update the
    corresponding attributes.  Missing fields will be set to ``None``.  The
    ``tenant_id`` on the record is immutable.
    """
    lead = get_lead(db, tenant_id=tenant_id, lead_id=lead_id)
    # Keep copy of original values for change detection
    original = {
        "first_name": lead.first_name,
        "middle_name": lead.middle_name,
        "last_name": lead.last_name,
        "source": lead.source,
        "lead_data": copy.deepcopy(lead.lead_data),
    }
    # Update fields
    lead.first_name = lead_in.first_name
    lead.middle_name = lead_in.middle_name
    lead.last_name = lead_in.last_name
    lead.source = lead_in.source
    lead.lead_data = (
        lead_in.lead_data.model_dump() if getattr(lead_in, "lead_data", None) else None
    )
    lead.updated_by = modified_user
    lead.updated_at = datetime.utcnow()
    db.add(lead)
    # Commit and refresh using centralized error handling
    commit_or_raise(db, refresh=lead, action="update_lead")
    logger.info("Updated lead %s for tenant %s", lead.id, tenant_id)
    # Determine changes
    changes: Dict[str, Any] = {}
    if original["first_name"] != lead.first_name:
        changes["first_name"] = lead.first_name
    if original["middle_name"] != lead.middle_name:
        changes["middle_name"] = lead.middle_name
    if original["last_name"] != lead.last_name:
        changes["last_name"] = lead.last_name
    if original["source"] != lead.source:
        changes["source"] = lead.source
    if original["lead_data"] != lead.lead_data:
        changes["lead_data"] = lead.lead_data
    # Emit update event if changes occurred
    if changes:
        snapshot = _lead_snapshot(lead)
        try:
            LeadProducer.send_lead_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=snapshot,
            )
        except Exception:
            logger.exception(
                "Failed to publish lead.updated event tenant_id=%s lead_id=%s",
                tenant_id,
                lead.id,
            )
    return lead


def apply_patch_operation(lead: Lead, op: JsonPatchOperation) -> None:
    """Apply a single JSON Patch operation on a Lead instance.

    Supports paths to top‑level scalar fields and nested JSON within the
    ``lead_data`` object.  ``replace`` and ``add`` operations assign values,
    while ``remove`` operations delete keys or array elements.  Removal of
    top‑level attributes is disallowed.
    """
    # Normalize path and split into parts
    path = op.path.lstrip("/")
    parts = path.split("/") if path else []
    if not parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid patch path",
        )

    root_field = parts[0]
    # Handle patching of nested lead_data
    if root_field == "lead_data":
        # Ensure lead_data is a dict
        if lead.lead_data is None:
            lead.lead_data = {}
        target: Any = lead.lead_data
        # Traverse into the nested path
        for segment in parts[1:-1]:
            # If segment is an array index
            if segment.isdigit():
                idx = int(segment)
                if not isinstance(target, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected list at '{'/'.join(parts[:-1])}'",
                    )
                if idx < 0 or idx >= len(target):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Index out of range at '{op.path}'",
                    )
                target = target[idx]
            else:
                # Dict traversal
                if not isinstance(target, dict):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected object at '{'/'.join(parts[:-1])}'",
                    )
                if segment not in target:
                    # Create nested container on the fly for add/replace
                    target[segment] = {} if not parts[parts.index(segment)+1].isdigit() else []  # type: ignore
                target = target[segment]
        final_segment = parts[-1]
        # At final segment, apply operation
        if op.op in ["replace", "add"]:
            if final_segment.isdigit():
                # Replace/add array element
                idx = int(final_segment)
                if not isinstance(target, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected list at '{'/'.join(parts[:-1])}'",
                    )
                # Expand list if necessary for add at index equal to length
                if op.op == "add" and idx == len(target):
                    target.append(op.value)
                elif idx < len(target):
                    target[idx] = op.value
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Index out of range at '{op.path}'",
                    )
            else:
                # Replace/add dictionary key
                if not isinstance(target, dict):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected object at '{'/'.join(parts[:-1])}'",
                    )
                target[final_segment] = op.value
        elif op.op == "remove":
            if final_segment.isdigit():
                idx = int(final_segment)
                if not isinstance(target, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected list at '{'/'.join(parts[:-1])}'",
                    )
                if 0 <= idx < len(target):
                    target.pop(idx)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Index out of range at '{op.path}'",
                    )
            else:
                if not isinstance(target, dict):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Expected object at '{'/'.join(parts[:-1])}'",
                    )
                if final_segment in target:
                    target.pop(final_segment)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Key '{final_segment}' does not exist",
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported operation: {op.op}",
            )
    else:
        # Top level scalar fields
        if op.op in ["replace", "add"]:
            if hasattr(lead, root_field):
                setattr(lead, root_field, op.value)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid field: {root_field}",
                )
        elif op.op == "remove":
            # Do not allow removal of required top level attributes
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot remove required attribute '{root_field}' from lead.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported operation: {op.op}",
            )


def patch_lead(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    patch_request: JsonPatchRequest,
    modified_user: str,
) -> Lead:
    """Apply a JSON Patch document to a lead.

    Patching is atomic – if any operation fails validation, the entire
    transaction is rolled back and an error is raised.  After all
    operations succeed the lead is committed and an update event is
    emitted with the set of changes.
    """
    lead = get_lead(db, tenant_id=tenant_id, lead_id=lead_id)
    # Capture original values for change computation
    original = {
        "first_name": lead.first_name,
        "middle_name": lead.middle_name,
        "last_name": lead.last_name,
        "source": lead.source,
        "lead_data": copy.deepcopy(lead.lead_data),
    }
    try:
        for operation in patch_request.operations:
            apply_patch_operation(lead, operation)
        # Update audit fields
        lead.updated_by = modified_user
        lead.updated_at = datetime.utcnow()
        db.add(lead)
        # Commit and refresh using centralized error handling
        commit_or_raise(db, refresh=lead, action="patch_lead")
    except HTTPException:
        # Rollback for validation errors
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error applying patch: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to apply patch")
    # Compute changes
    changes: Dict[str, Any] = {}
    if original["first_name"] != lead.first_name:
        changes["first_name"] = lead.first_name
    if original["middle_name"] != lead.middle_name:
        changes["middle_name"] = lead.middle_name
    if original["last_name"] != lead.last_name:
        changes["last_name"] = lead.last_name
    if original["source"] != lead.source:
        changes["source"] = lead.source
    if original["lead_data"] != lead.lead_data:
        changes["lead_data"] = lead.lead_data
    # Emit update event if changes occurred
    if changes:
        snapshot = _lead_snapshot(lead)
        try:
            LeadProducer.send_lead_updated(
                tenant_id=tenant_id,
                changes=changes,
                payload=snapshot,
            )
        except Exception:
            logger.exception(
                "Failed to publish lead.updated event tenant_id=%s lead_id=%s",
                tenant_id,
                lead.id,
            )
    return lead


def delete_lead(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
) -> None:
    """Delete a lead from the database.

    Returns ``None`` on success and raises HTTP 404 if the lead is not
    found or does not belong to the tenant.  An event is emitted after
    deletion is committed.
    """
    lead = get_lead(db, tenant_id=tenant_id, lead_id=lead_id)
    db.delete(lead)
    # Commit deletion using centralized error handling
    commit_or_raise(db, action="delete_lead")
    logger.info("Deleted lead %s for tenant %s", lead.id, tenant_id)
    try:
        LeadProducer.send_lead_deleted(
            tenant_id=tenant_id,
            deleted_dt=datetime.utcnow().isoformat(),
        )
    except Exception:
        logger.exception(
            "Failed to publish lead.deleted event tenant_id=%s lead_id=%s",
            tenant_id,
            lead.id,
        )
    return None