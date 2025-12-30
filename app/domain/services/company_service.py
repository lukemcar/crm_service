"""
Service layer for managing Company entities and their nested resources.

This module provides CRUD operations for companies along with helpers to
manage nested collections such as phone numbers, emails, addresses,
social profiles, notes, and relationships.  JSON Patch operations
are supported on both top‑level fields and nested objects.  Events are
emitted after each mutation using dedicated producers.

CompanyRelationship and ContactCompanyRelationship changes are
handled via dedicated functions and emit their own event types.  They
do not contribute to the company update delta.  Contact‑company
relationships are managed from the company side via the company
contacts endpoint.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Import the CRM domain models rather than relying on placeholder names.
from app.domain.models.company import Company
from app.domain.models.company_phone import CompanyPhone
from app.domain.models.company_email import CompanyEmail
from app.domain.models.company_address import CompanyAddress
from app.domain.models.company_social_profile import CompanySocialProfile
from app.domain.models.company_note import CompanyNote
from app.domain.models.company_relationship import CompanyRelationship
from app.domain.models.contact_company_relationship import ContactCompanyRelationship

# Import the Pydantic schemas for companies from the CRM package.
from app.domain.schemas.company import (
    TenantCreateCompany,
    AdminCreateCompany,
    CompanySearchCriteria,
    CompanyPhoneNumberCreateRequest,
    CompanyPhoneNumberUpdateRequest,
    CompanyEmailCreateRequest,
    CompanyEmailUpdateRequest,
    CompanyAddressCreateRequest,
    CompanyAddressUpdateRequest,
    CompanySocialProfileCreateRequest,
    CompanySocialProfileUpdateRequest,
    CompanyNoteCreateRequest,
    CompanyNoteUpdateRequest,
    CompanyRelationshipCreateRequest,
    CompanyRelationshipUpdateRequest,
    CompanyContactRelationshipCreateRequest,
    CompanyContactRelationshipUpdateRequest,
)

# Import event models and message producers from their correct locations.
from app.domain.schemas.events.company_event import CompanyDelta
from app.messaging.producers.company_producer import CompanyMessageProducer as CompanyProducer
from app.messaging.producers.company_relationship_producer import (
    CompanyRelationshipMessageProducer as CompanyRelationshipProducer,
)
from app.messaging.producers.contact_company_relationship_producer import (
    ContactCompanyRelationshipMessageProducer as ContactCompanyRelationshipProducer,
)
from app.domain.schemas.json_patch import JsonPatchRequest, JsonPatchOperation

logger = logging.getLogger("company_service")


# ---------------------------------------------------------------------------
# Helper functions for snapshots and delta computation
# ---------------------------------------------------------------------------


def _phone_snapshot(phone: CompanyPhone) -> Dict[str, Any]:
    return {
        "id": phone.id,
        "phone_raw": phone.phone_raw,
        "phone_e164": phone.phone_e164,
        "phone_ext": phone.phone_ext,
        "phone_type": phone.phone_type,
        "is_primary": phone.is_primary,
        "is_sms_capable": phone.is_sms_capable,
        "is_verified": phone.is_verified,
        "verified_at": phone.verified_at.isoformat() if phone.verified_at else None,
        "created_at": phone.created_at.isoformat() if phone.created_at else None,
        "updated_at": phone.updated_at.isoformat() if phone.updated_at else None,
        "created_by": str(phone.created_by) if phone.created_by else None,
        "updated_by": str(phone.updated_by) if phone.updated_by else None,
    }


def _email_snapshot(email: CompanyEmail) -> Dict[str, Any]:
    return {
        "id": email.id,
        "email": email.email,
        "email_type": email.email_type,
        "is_primary": email.is_primary,
        "is_verified": email.is_verified,
        "verified_at": email.verified_at.isoformat() if email.verified_at else None,
        "created_at": email.created_at.isoformat() if email.created_at else None,
        "updated_at": email.updated_at.isoformat() if email.updated_at else None,
        "created_by": str(email.created_by) if email.created_by else None,
        "updated_by": str(email.updated_by) if email.updated_by else None,
    }


def _address_snapshot(address: CompanyAddress) -> Dict[str, Any]:
    return {
        "id": address.id,
        "address_type": address.address_type,
        "label": address.label,
        "is_primary": address.is_primary,
        "line1": address.line1,
        "line2": address.line2,
        "line3": address.line3,
        "city": address.city,
        "region": address.region,
        "postal_code": address.postal_code,
        "country_code": address.country_code,
        "created_at": address.created_at.isoformat() if address.created_at else None,
        "updated_at": address.updated_at.isoformat() if address.updated_at else None,
        "created_by": str(address.created_by) if address.created_by else None,
        "updated_by": str(address.updated_by) if address.updated_by else None,
    }


def _social_profile_snapshot(profile: CompanySocialProfile) -> Dict[str, Any]:
    return {
        "id": profile.id,
        "profile_type": profile.profile_type,
        "profile_url": profile.profile_url,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        "created_by": str(profile.created_by) if profile.created_by else None,
        "updated_by": str(profile.updated_by) if profile.updated_by else None,
    }


def _note_snapshot(note: CompanyNote) -> Dict[str, Any]:
    return {
        "id": note.id,
        "note_type": note.note_type,
        "title": note.title,
        "body": note.body,
        "noted_at": note.noted_at.isoformat() if note.noted_at else None,
        "source_system": note.source_system,
        "source_ref": note.source_ref,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        "created_by": str(note.created_by) if note.created_by else None,
        "updated_by": str(note.updated_by) if note.updated_by else None,
    }


def _relationship_snapshot(rel: CompanyRelationship) -> Dict[str, Any]:
    return {
        "id": rel.id,
        "from_company_id": rel.from_company_id,
        "to_company_id": rel.to_company_id,
        "from_role": rel.from_role,
        "to_role": rel.to_role,
        "is_active": rel.is_active,
        "start_date": rel.start_date.isoformat() if rel.start_date else None,
        "end_date": rel.end_date.isoformat() if rel.end_date else None,
        "notes": rel.notes,
        "created_at": rel.created_at.isoformat() if rel.created_at else None,
        "updated_at": rel.updated_at.isoformat() if rel.updated_at else None,
        "created_by": rel.created_by,
        "updated_by": rel.updated_by,
    }


def _contact_rel_snapshot(rel: ContactCompanyRelationship) -> Dict[str, Any]:
    return {
        "id": rel.id,
        "contact_id": rel.contact_id,
        "company_id": rel.company_id,
        "relationship_type": rel.relationship_type,
        "department": rel.department,
        "job_title": rel.job_title,
        "work_email": rel.work_email,
        "work_phone_raw": rel.work_phone_raw,
        "work_phone_e164": rel.work_phone_e164,
        "work_phone_ext": rel.work_phone_ext,
        "is_primary": rel.is_primary,
        "start_date": rel.start_date.isoformat() if rel.start_date else None,
        "end_date": rel.end_date.isoformat() if rel.end_date else None,
        "is_active": rel.is_active,
        "created_at": rel.created_at.isoformat() if rel.created_at else None,
        "updated_at": rel.updated_at.isoformat() if rel.updated_at else None,
        "created_by": rel.created_by,
        "updated_by": rel.updated_by,
    }


def _company_snapshot(company: Any) -> Dict[str, Any]:
    """Return a full snapshot of a company including nested resources."""
    return {
        "id": company.id,
        "tenant_id": company.tenant_id,
        "name": getattr(company, "name", None),
        "legal_name": getattr(company, "legal_name", None),
        "industry": getattr(company, "industry", None),
        "website": getattr(company, "website", None),
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "updated_at": company.updated_at.isoformat() if company.updated_at else None,
        "created_by": getattr(company, "created_by", None),
        "updated_by": getattr(company, "updated_by", None),
        "phones": [_phone_snapshot(p) for p in getattr(company, "phones", [])],
        "emails": [_email_snapshot(e) for e in getattr(company, "emails", [])],
        "addresses": [_address_snapshot(a) for a in getattr(company, "addresses", [])],
        "social_profiles": [_social_profile_snapshot(s) for s in getattr(company, "social_profiles", [])],
        "notes": [_note_snapshot(n) for n in getattr(company, "notes", [])],
        "relationships": [_relationship_snapshot(r) for r in getattr(company, "relationships_from", [])],
        "contact_relationships": [_contact_rel_snapshot(c) for c in getattr(company, "contact_relationships", [])],
    }


# ---------------------------------------------------------------------------
# CRUD for companies
# ---------------------------------------------------------------------------


def list_companies(
    db: Session,
    *,
    tenant_id: Optional[uuid.UUID],
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    contact_name: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Tuple[List[Any], int]:
    """Return a list of companies filtered by optional search criteria.

    The ``tenant_id`` parameter scopes the search to a single tenant when
    provided.  Filters perform case‑insensitive substring matching on
    company name.  Phone and email filters perform substring matches
    against nested phone and email values.  Contact name search
    matches the contact_id associated with contact_company_relationships
    by joining across relationships.
    """
    if Company is None:
        return ([], 0)
    query = db.query(Company)
    if tenant_id:
        query = query.filter(Company.tenant_id == tenant_id)
    if name:
        # The Company model uses ``company_name`` instead of ``name``.  Use
        # the correct attribute for case‑insensitive matching.
        query = query.filter(Company.company_name.ilike(f"%{name}%"))
    # Join to phones/emails for search
    if phone:
        query = query.join(Company.phones).filter(
            (CompanyPhone.phone_raw.ilike(f"%{phone}%"))
            | (CompanyPhone.phone_e164.ilike(f"%{phone}%"))
        )
    if email:
        query = query.join(Company.emails).filter(CompanyEmail.email.ilike(f"%{email}%"))
    if contact_name:
        # Join through contact_company_relationship to contacts to perform name
        # matching.  Import the Contact model from the CRM package rather
        # than relying on a fallback.  Filter on first_name and last_name
        # attributes for case‑insensitive matches.
        query = query.join(Company.contact_relationships).join(ContactCompanyRelationship.contact)
        from app.domain.models.contact import Contact  # type: ignore  # circular import safe at runtime
        query = query.filter(
            (Contact.first_name.ilike(f"%{contact_name}%"))
            | (Contact.last_name.ilike(f"%{contact_name}%"))
        )
    total = query.count()
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    query = query.order_by(Company.created_at.desc())
    return (query.all(), total)


def get_company(db: Session, *, tenant_id: Optional[uuid.UUID], company_id: uuid.UUID) -> Any:
    """Retrieve a company by its ID and optional tenant ID."""
    if Company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    q = db.query(Company).filter(Company.id == company_id)
    if tenant_id:
        q = q.filter(Company.tenant_id == tenant_id)
    company = q.first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def create_company(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    request: TenantCreateCompany | AdminCreateCompany,
    created_by: Optional[str] = None,
) -> Any:
    """Create a new company along with any nested collections."""
    if Company is None:
        raise HTTPException(status_code=500, detail="Company model not loaded")
    # Instantiate base company.
    #
    # The ORM Company model defines ``company_name`` and ``domain`` rather than
    # ``name`` and ``website``.  Map the incoming Pydantic fields to the
    # corresponding ORM attributes.  The ``id`` column is generated by
    # default, so it is not explicitly set here.  Audit timestamps are
    # populated manually to align with the rest of the service functions.
    company = Company(
        tenant_id=tenant_id,
        company_name=request.name,
        domain=getattr(request, "website", None),
        industry=getattr(request, "industry", None),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=created_by,
        updated_by=created_by,
    )
    # Initialize nested collections
    for phone_in in request.phones or []:
        phone = CompanyPhone(
            tenant_id=tenant_id,
            company_id=company.id,
            phone_raw=phone_in.phone_raw,
            phone_e164=phone_in.phone_e164,
            phone_ext=phone_in.phone_ext,
            phone_type=phone_in.phone_type or "main",
            is_primary=phone_in.is_primary or False,
            is_sms_capable=phone_in.is_sms_capable or False,
            is_verified=phone_in.is_verified or False,
            created_by=created_by,
            updated_by=created_by,
        )
        company.phones.append(phone)
    for email_in in request.emails or []:
        email = CompanyEmail(
            tenant_id=tenant_id,
            company_id=company.id,
            email=email_in.email,
            email_type=email_in.email_type or "work",
            is_primary=email_in.is_primary or False,
            is_verified=email_in.is_verified or False,
            created_by=created_by,
            updated_by=created_by,
        )
        company.emails.append(email)
    for addr_in in request.addresses or []:
        addr = CompanyAddress(
            tenant_id=tenant_id,
            company_id=company.id,
            address_type=addr_in.address_type or "office",
            label=addr_in.label,
            is_primary=addr_in.is_primary or False,
            line1=addr_in.line1,
            line2=addr_in.line2,
            line3=getattr(addr_in, "line3", None),
            city=addr_in.city,
            region=addr_in.region,
            postal_code=addr_in.postal_code,
            country_code=addr_in.country_code or "US",
            created_by=created_by,
            updated_by=created_by,
        )
        company.addresses.append(addr)
    for social_in in request.social_profiles or []:
        social = CompanySocialProfile(
            tenant_id=tenant_id,
            company_id=company.id,
            profile_type=social_in.profile_type,
            profile_url=social_in.profile_url,
            created_by=created_by,
            updated_by=created_by,
        )
        company.social_profiles.append(social)
    for note_in in request.notes or []:
        note = CompanyNote(
            tenant_id=tenant_id,
            company_id=company.id,
            note_type=note_in.note_type or "note",
            title=note_in.title,
            body=note_in.body,
            noted_at=note_in.noted_at or datetime.utcnow(),
            source_system=note_in.source_system,
            source_ref=note_in.source_ref,
            created_by=created_by,
            updated_by=created_by,
        )
        company.notes.append(note)
    db.add(company)
    db.commit()
    db.refresh(company)
    # Emit event
    snapshot = _company_snapshot(company)
    CompanyProducer.send_company_created(tenant_id=tenant_id, payload=snapshot)
    return company


def delete_company(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> None:
    """Delete a company."""
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    db.delete(company)
    db.commit()
    # Emit deletion event
    CompanyProducer.send_company_deleted(tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# JSON Patch support
# ---------------------------------------------------------------------------


def patch_company(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    patch_request: JsonPatchRequest,
    updated_by: Optional[str] = None,
) -> Any:
    """Apply a JSON Patch document to a company.

    Supports updating top‑level attributes as well as nested
    collections.  Nested objects are identified by their UUID in the
    path (e.g. ``/phones/<phone_id>/phone_raw``).  Adding new nested
    objects is supported via a path of ``/phones`` with an object
    value.  CompanyRelationship and ContactCompanyRelationship
    endpoints must be used for those relationships; they are not
    supported via JSON Patch.
    """
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    # Build delta accumulator
    delta = CompanyDelta()

    # Handlers for base and collection
    def handle_base_patch(field_name: str, operation: JsonPatchOperation) -> None:
        """
        Handle JSON Patch operations for top‑level company fields.

        The external API uses field names defined in the Pydantic models
        (e.g. ``name`` and ``website``) whereas the ORM model uses
        ``company_name`` and ``domain``.  Translate incoming field
        names to the ORM attributes before applying changes.
        """
        # Map external field names to internal ORM attributes
        field_map = {
            "name": "company_name",
            "website": "domain",
        }
        internal_field = field_map.get(field_name, field_name)
        if operation.op in ("add", "replace"):
            if not hasattr(company, internal_field):
                raise HTTPException(status_code=400, detail=f"Invalid field: {field_name}")
            old_val = getattr(company, internal_field)
            new_val = operation.value
            setattr(company, internal_field, new_val)
            if old_val != new_val:
                if delta.base_fields is None:
                    delta.base_fields = {}
                delta.base_fields[internal_field] = new_val
        elif operation.op == "remove":
            if not hasattr(company, internal_field):
                raise HTTPException(status_code=400, detail=f"Invalid field: {field_name}")
            setattr(company, internal_field, None)
            if delta.base_fields is None:
                delta.base_fields = {}
            delta.base_fields[internal_field] = None
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported op: {operation.op}")

    def record_delta(action: str, collection_name: str, payload: Any) -> None:
        attr = None
        if collection_name == "phones":
            if action == "add":
                attr = "phones_added"
            elif action == "update":
                attr = "phones_updated"
            elif action == "delete":
                attr = "phones_deleted"
        elif collection_name == "emails":
            if action == "add":
                attr = "emails_added"
            elif action == "update":
                attr = "emails_updated"
            elif action == "delete":
                attr = "emails_deleted"
        elif collection_name == "addresses":
            if action == "add":
                attr = "addresses_added"
            elif action == "update":
                attr = "addresses_updated"
            elif action == "delete":
                attr = "addresses_deleted"
        elif collection_name == "social_profiles":
            if action == "add":
                attr = "social_profiles_added"
            elif action == "update":
                attr = "social_profiles_updated"
            elif action == "delete":
                attr = "social_profiles_deleted"
        elif collection_name == "notes":
            if action == "add":
                attr = "notes_added"
            elif action == "update":
                attr = "notes_updated"
            elif action == "delete":
                attr = "notes_deleted"
        if attr:
            current = getattr(delta, attr)
            if current is None:
                setattr(delta, attr, [payload])
            else:
                current.append(payload)

    def handle_collection_patch(collection: str, parts: List[str], operation: JsonPatchOperation) -> None:
        # Determine model class, snapshot function and update models
        if collection == "phones":
            model_cls = CompanyPhone
            snapshot_fn = _phone_snapshot
            create_model = CompanyPhoneNumberCreateRequest
            update_model = CompanyPhoneNumberUpdateRequest
        elif collection == "emails":
            model_cls = CompanyEmail
            snapshot_fn = _email_snapshot
            create_model = CompanyEmailCreateRequest
            update_model = CompanyEmailUpdateRequest
        elif collection == "addresses":
            model_cls = CompanyAddress
            snapshot_fn = _address_snapshot
            create_model = CompanyAddressCreateRequest
            update_model = CompanyAddressUpdateRequest
        elif collection == "social_profiles":
            model_cls = CompanySocialProfile
            snapshot_fn = _social_profile_snapshot
            create_model = CompanySocialProfileCreateRequest
            update_model = CompanySocialProfileUpdateRequest
        elif collection == "notes":
            model_cls = CompanyNote
            snapshot_fn = _note_snapshot
            create_model = CompanyNoteCreateRequest
            update_model = CompanyNoteUpdateRequest
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported collection: {collection}")

        # If adding at collection root
        if len(parts) == 1:
            if operation.op not in ("add", "replace"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Operation {operation.op} not supported at collection root",
                )
            if not isinstance(operation.value, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"Value must be an object when adding to {collection}",
                )
            # Validate create payload
            create_in = create_model.model_validate(operation.value)
            if collection == "phones":
                obj = model_cls(
                    tenant_id=tenant_id,
                    company_id=company.id,
                    phone_raw=create_in.phone_raw,
                    phone_e164=create_in.phone_e164,
                    phone_ext=create_in.phone_ext,
                    phone_type=create_in.phone_type or "main",
                    is_primary=create_in.is_primary or False,
                    is_sms_capable=create_in.is_sms_capable or False,
                    is_verified=create_in.is_verified or False,
                    created_by=updated_by,
                    updated_by=updated_by,
                )
            elif collection == "emails":
                obj = model_cls(
                    tenant_id=tenant_id,
                    company_id=company.id,
                    email=create_in.email,
                    email_type=create_in.email_type or "work",
                    is_primary=create_in.is_primary or False,
                    is_verified=create_in.is_verified or False,
                    created_by=updated_by,
                    updated_by=updated_by,
                )
            elif collection == "addresses":
                obj = model_cls(
                    tenant_id=tenant_id,
                    company_id=company.id,
                    address_type=create_in.address_type or "office",
                    label=create_in.label,
                    is_primary=create_in.is_primary or False,
                    line1=create_in.line1,
                    line2=create_in.line2,
                    line3=getattr(create_in, "line3", None),
                    city=create_in.city,
                    region=create_in.region,
                    postal_code=create_in.postal_code,
                    country_code=create_in.country_code or "US",
                    created_by=updated_by,
                    updated_by=updated_by,
                )
            elif collection == "social_profiles":
                obj = model_cls(
                    tenant_id=tenant_id,
                    company_id=company.id,
                    profile_type=create_in.profile_type,
                    profile_url=create_in.profile_url,
                    created_by=updated_by,
                    updated_by=updated_by,
                )
            elif collection == "notes":
                obj = model_cls(
                    tenant_id=tenant_id,
                    company_id=company.id,
                    note_type=create_in.note_type or "note",
                    title=create_in.title,
                    body=create_in.body,
                    noted_at=create_in.noted_at or datetime.utcnow(),
                    source_system=create_in.source_system,
                    source_ref=create_in.source_ref,
                    created_by=updated_by,
                    updated_by=updated_by,
                )
            else:
                raise HTTPException(status_code=400, detail="Unsupported collection")
            db.add(obj)
            db.flush()
            getattr(company, collection).append(obj)
            record_delta("add", collection, snapshot_fn(obj))
            return

        # Otherwise we have an id at parts[1]
        obj_id = parts[1]
        try:
            obj_uuid = uuid.UUID(obj_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid UUID: {obj_id}")
        # Find existing object
        found = None
        for item in getattr(company, collection):
            if item.id == obj_uuid:
                found = item
                break
        if found is None:
            raise HTTPException(status_code=404, detail=f"{collection[:-1].title()} not found")
        # If operation targets the entire object (length == 2)
        if len(parts) == 2:
            if operation.op == "remove":
                db.delete(found)
                record_delta("delete", collection, found.id)
                return
            elif operation.op in ("add", "replace"):
                if not isinstance(operation.value, dict):
                    raise HTTPException(status_code=400, detail="Value must be an object for update")
                update_in = update_model.model_validate(operation.value)
                # Update each provided field
                if collection == "phones":
                    if update_in.phone_raw is not None:
                        found.phone_raw = update_in.phone_raw
                    if update_in.phone_e164 is not None:
                        found.phone_e164 = update_in.phone_e164
                    if update_in.phone_ext is not None:
                        found.phone_ext = update_in.phone_ext
                    if update_in.phone_type is not None:
                        found.phone_type = update_in.phone_type
                    if update_in.is_primary is not None:
                        found.is_primary = update_in.is_primary
                    if update_in.is_sms_capable is not None:
                        found.is_sms_capable = update_in.is_sms_capable
                    if update_in.is_verified is not None:
                        found.is_verified = update_in.is_verified
                elif collection == "emails":
                    if update_in.email is not None:
                        found.email = update_in.email
                    if update_in.email_type is not None:
                        found.email_type = update_in.email_type
                    if update_in.is_primary is not None:
                        found.is_primary = update_in.is_primary
                    if update_in.is_verified is not None:
                        found.is_verified = update_in.is_verified
                elif collection == "addresses":
                    if update_in.address_type is not None:
                        found.address_type = update_in.address_type
                    if update_in.label is not None:
                        found.label = update_in.label
                    if update_in.is_primary is not None:
                        found.is_primary = update_in.is_primary
                    if update_in.line1 is not None:
                        found.line1 = update_in.line1
                    if update_in.line2 is not None:
                        found.line2 = update_in.line2
                    if update_in.line3 is not None:
                        found.line3 = update_in.line3
                    if update_in.city is not None:
                        found.city = update_in.city
                    if update_in.region is not None:
                        found.region = update_in.region
                    if update_in.postal_code is not None:
                        found.postal_code = update_in.postal_code
                    if update_in.country_code is not None:
                        found.country_code = update_in.country_code
                elif collection == "social_profiles":
                    if update_in.profile_type is not None:
                        found.profile_type = update_in.profile_type
                    if update_in.profile_url is not None:
                        found.profile_url = update_in.profile_url
                elif collection == "notes":
                    if update_in.note_type is not None:
                        found.note_type = update_in.note_type
                    if update_in.title is not None:
                        found.title = update_in.title
                    if update_in.body is not None:
                        found.body = update_in.body
                    if update_in.noted_at is not None:
                        found.noted_at = update_in.noted_at
                    if update_in.source_system is not None:
                        found.source_system = update_in.source_system
                    if update_in.source_ref is not None:
                        found.source_ref = update_in.source_ref
                # Record update
                found.updated_at = datetime.utcnow()
                found.updated_by = updated_by
                record_delta("update", collection, snapshot_fn(found))
                return
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported op: {operation.op}")
        # Otherwise nested attribute path (len(parts) >= 3)
        # We treat any deeper patch as update of specific attribute if allowed
        attr_name = parts[2] if len(parts) > 2 else None
        if operation.op in ("add", "replace"):
            if not hasattr(found, attr_name):
                raise HTTPException(status_code=400, detail=f"Invalid attribute: {attr_name}")
            setattr(found, attr_name, operation.value)
            found.updated_at = datetime.utcnow()
            found.updated_by = updated_by
            record_delta("update", collection, snapshot_fn(found))
            return
        elif operation.op == "remove":
            # Setting attribute to None for remove operations if nullable
            if not hasattr(found, attr_name):
                raise HTTPException(status_code=400, detail=f"Invalid attribute: {attr_name}")
            setattr(found, attr_name, None)
            found.updated_at = datetime.utcnow()
            found.updated_by = updated_by
            record_delta("update", collection, snapshot_fn(found))
            return
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported op: {operation.op}")

    # Iterate operations
    for operation in patch_request.operations:
        parts = operation.path.strip("/").split("/")
        if not parts or parts[0] == "":
            raise HTTPException(status_code=400, detail="Invalid path")
        field_name = parts[0]
        # Determine if nested collection
        if field_name in {"phones", "emails", "addresses", "social_profiles", "notes"}:
            handle_collection_patch(field_name, parts, operation)
        else:
            handle_base_patch(field_name, operation)

    # Update timestamps and user
    company.updated_at = datetime.utcnow()
    company.updated_by = updated_by
    db.add(company)
    db.commit()
    db.refresh(company)
    # Emit update event
    snapshot = _company_snapshot(company)
    CompanyProducer.send_company_updated(tenant_id=tenant_id, changes=delta, payload=snapshot)
    return company


# ---------------------------------------------------------------------------
# Nested resource list functions
# ---------------------------------------------------------------------------


def list_company_phones(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[CompanyPhone]:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    return list(company.phones)


def list_company_emails(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[CompanyEmail]:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    return list(company.emails)


def list_company_addresses(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[CompanyAddress]:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    return list(company.addresses)


def list_company_social_profiles(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[CompanySocialProfile]:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    return list(company.social_profiles)


def list_company_notes(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[CompanyNote]:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    return list(company.notes)


def list_company_relationships(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[CompanyRelationship]:
    # Relationships where from_company_id == company_id
    return (
        db.query(CompanyRelationship)
        .filter(CompanyRelationship.tenant_id == tenant_id, CompanyRelationship.from_company_id == company_id)
        .all()
    )


def list_company_contacts(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> List[ContactCompanyRelationship]:
    return (
        db.query(ContactCompanyRelationship)
        .filter(ContactCompanyRelationship.tenant_id == tenant_id, ContactCompanyRelationship.company_id == company_id)
        .all()
    )


# ---------------------------------------------------------------------------
# Nested resource mutation functions
# ---------------------------------------------------------------------------


def add_company_phone(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    phone_in: CompanyPhoneNumberCreateRequest,
    updated_by: Optional[str] = None,
) -> CompanyPhone:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    phone = CompanyPhone(
        tenant_id=tenant_id,
        company_id=company.id,
        phone_raw=phone_in.phone_raw,
        phone_e164=phone_in.phone_e164,
        phone_ext=phone_in.phone_ext,
        phone_type=phone_in.phone_type or "main",
        is_primary=phone_in.is_primary or False,
        is_sms_capable=phone_in.is_sms_capable or False,
        is_verified=phone_in.is_verified or False,
        created_by=updated_by,
        updated_by=updated_by,
    )
    company.phones.append(phone)
    db.add(phone)
    db.commit()
    db.refresh(phone)
    # Emit update event
    delta = CompanyDelta(phones_added=[_phone_snapshot(phone)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return phone


def update_company_phone(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    phone_id: uuid.UUID,
    phone_update: CompanyPhoneNumberUpdateRequest,
    updated_by: Optional[str] = None,
) -> CompanyPhone:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    phone = next((p for p in company.phones if p.id == phone_id), None)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")
    changed = {}
    if phone_update.phone_raw is not None:
        phone.phone_raw = phone_update.phone_raw
        changed["phone_raw"] = phone_update.phone_raw
    if phone_update.phone_e164 is not None:
        phone.phone_e164 = phone_update.phone_e164
        changed["phone_e164"] = phone_update.phone_e164
    if phone_update.phone_ext is not None:
        phone.phone_ext = phone_update.phone_ext
        changed["phone_ext"] = phone_update.phone_ext
    if phone_update.phone_type is not None:
        phone.phone_type = phone_update.phone_type
        changed["phone_type"] = phone_update.phone_type
    if phone_update.is_primary is not None:
        phone.is_primary = phone_update.is_primary
        changed["is_primary"] = phone_update.is_primary
    if phone_update.is_sms_capable is not None:
        phone.is_sms_capable = phone_update.is_sms_capable
        changed["is_sms_capable"] = phone_update.is_sms_capable
    if phone_update.is_verified is not None:
        phone.is_verified = phone_update.is_verified
        changed["is_verified"] = phone_update.is_verified
    phone.updated_at = datetime.utcnow()
    phone.updated_by = updated_by
    db.add(phone)
    db.commit()
    db.refresh(phone)
    # Emit update delta
    delta = CompanyDelta(phones_updated=[_phone_snapshot(phone)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return phone


def delete_company_phone(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    phone_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    phone = next((p for p in company.phones if p.id == phone_id), None)
    if phone is None:
        raise HTTPException(status_code=404, detail="Phone not found")
    db.delete(phone)
    db.commit()
    # Emit delta
    delta = CompanyDelta(phones_deleted=[phone.id])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return None


def add_company_email(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    email_in: CompanyEmailCreateRequest,
    updated_by: Optional[str] = None,
) -> CompanyEmail:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    email = CompanyEmail(
        tenant_id=tenant_id,
        company_id=company.id,
        email=email_in.email,
        email_type=email_in.email_type or "work",
        is_primary=email_in.is_primary or False,
        is_verified=email_in.is_verified or False,
        created_by=updated_by,
        updated_by=updated_by,
    )
    company.emails.append(email)
    db.add(email)
    db.commit()
    db.refresh(email)
    delta = CompanyDelta(emails_added=[_email_snapshot(email)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return email


def update_company_email(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    email_id: uuid.UUID,
    email_update: CompanyEmailUpdateRequest,
    updated_by: Optional[str] = None,
) -> CompanyEmail:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    email = next((e for e in company.emails if e.id == email_id), None)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    changed = {}
    if email_update.email is not None:
        email.email = email_update.email
        changed["email"] = email_update.email
    if email_update.email_type is not None:
        email.email_type = email_update.email_type
        changed["email_type"] = email_update.email_type
    if email_update.is_primary is not None:
        email.is_primary = email_update.is_primary
        changed["is_primary"] = email_update.is_primary
    if email_update.is_verified is not None:
        email.is_verified = email_update.is_verified
        changed["is_verified"] = email_update.is_verified
    email.updated_at = datetime.utcnow()
    email.updated_by = updated_by
    db.add(email)
    db.commit()
    db.refresh(email)
    delta = CompanyDelta(emails_updated=[_email_snapshot(email)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return email


def delete_company_email(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    email_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    email = next((e for e in company.emails if e.id == email_id), None)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    db.delete(email)
    db.commit()
    delta = CompanyDelta(emails_deleted=[email.id])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return None


def add_company_address(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    addr_in: CompanyAddressCreateRequest,
    updated_by: Optional[str] = None,
) -> CompanyAddress:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    addr = CompanyAddress(
        tenant_id=tenant_id,
        company_id=company.id,
        address_type=addr_in.address_type or "office",
        label=addr_in.label,
        is_primary=addr_in.is_primary or False,
        line1=addr_in.line1,
        line2=addr_in.line2,
        line3=getattr(addr_in, "line3", None),
        city=addr_in.city,
        region=addr_in.region,
        postal_code=addr_in.postal_code,
        country_code=addr_in.country_code or "US",
        created_by=updated_by,
        updated_by=updated_by,
    )
    company.addresses.append(addr)
    db.add(addr)
    db.commit()
    db.refresh(addr)
    delta = CompanyDelta(addresses_added=[_address_snapshot(addr)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return addr


def update_company_address(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    address_id: uuid.UUID,
    addr_update: CompanyAddressUpdateRequest,
    updated_by: Optional[str] = None,
) -> CompanyAddress:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    addr = next((a for a in company.addresses if a.id == address_id), None)
    if addr is None:
        raise HTTPException(status_code=404, detail="Address not found")
    if addr_update.address_type is not None:
        addr.address_type = addr_update.address_type
    if addr_update.label is not None:
        addr.label = addr_update.label
    if addr_update.is_primary is not None:
        addr.is_primary = addr_update.is_primary
    if addr_update.line1 is not None:
        addr.line1 = addr_update.line1
    if addr_update.line2 is not None:
        addr.line2 = addr_update.line2
    if addr_update.line3 is not None:
        addr.line3 = addr_update.line3
    if addr_update.city is not None:
        addr.city = addr_update.city
    if addr_update.region is not None:
        addr.region = addr_update.region
    if addr_update.postal_code is not None:
        addr.postal_code = addr_update.postal_code
    if addr_update.country_code is not None:
        addr.country_code = addr_update.country_code
    addr.updated_at = datetime.utcnow()
    addr.updated_by = updated_by
    db.add(addr)
    db.commit()
    db.refresh(addr)
    delta = CompanyDelta(addresses_updated=[_address_snapshot(addr)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return addr


def delete_company_address(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    address_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    addr = next((a for a in company.addresses if a.id == address_id), None)
    if addr is None:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    delta = CompanyDelta(addresses_deleted=[addr.id])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return None


def add_company_social_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    profile_in: CompanySocialProfileCreateRequest,
    updated_by: Optional[str] = None,
) -> CompanySocialProfile:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    profile = CompanySocialProfile(
        tenant_id=tenant_id,
        company_id=company.id,
        profile_type=profile_in.profile_type,
        profile_url=profile_in.profile_url,
        created_by=updated_by,
        updated_by=updated_by,
    )
    company.social_profiles.append(profile)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    delta = CompanyDelta(social_profiles_added=[_social_profile_snapshot(profile)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return profile


def update_company_social_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    social_profile_id: uuid.UUID,
    profile_update: CompanySocialProfileUpdateRequest,
    updated_by: Optional[str] = None,
) -> CompanySocialProfile:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    profile = next((s for s in company.social_profiles if s.id == social_profile_id), None)
    if profile is None:
        raise HTTPException(status_code=404, detail="Social profile not found")
    if profile_update.profile_type is not None:
        profile.profile_type = profile_update.profile_type
    if profile_update.profile_url is not None:
        profile.profile_url = profile_update.profile_url
    profile.updated_at = datetime.utcnow()
    profile.updated_by = updated_by
    db.add(profile)
    db.commit()
    db.refresh(profile)
    delta = CompanyDelta(social_profiles_updated=[_social_profile_snapshot(profile)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return profile


def delete_company_social_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    social_profile_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    profile = next((s for s in company.social_profiles if s.id == social_profile_id), None)
    if profile is None:
        raise HTTPException(status_code=404, detail="Social profile not found")
    db.delete(profile)
    db.commit()
    delta = CompanyDelta(social_profiles_deleted=[profile.id])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return None


def add_company_note(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    note_in: CompanyNoteCreateRequest,
    updated_by: Optional[str] = None,
) -> CompanyNote:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    note = CompanyNote(
        tenant_id=tenant_id,
        company_id=company.id,
        note_type=note_in.note_type or "note",
        title=note_in.title,
        body=note_in.body,
        noted_at=note_in.noted_at or datetime.utcnow(),
        source_system=note_in.source_system,
        source_ref=note_in.source_ref,
        created_by=updated_by,
        updated_by=updated_by,
    )
    company.notes.append(note)
    db.add(note)
    db.commit()
    db.refresh(note)
    delta = CompanyDelta(notes_added=[_note_snapshot(note)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return note


def update_company_note(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    note_id: uuid.UUID,
    note_update: CompanyNoteUpdateRequest,
    updated_by: Optional[str] = None,
) -> CompanyNote:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    note = next((n for n in company.notes if n.id == note_id), None)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_update.note_type is not None:
        note.note_type = note_update.note_type
    if note_update.title is not None:
        note.title = note_update.title
    if note_update.body is not None:
        note.body = note_update.body
    if note_update.noted_at is not None:
        note.noted_at = note_update.noted_at
    if note_update.source_system is not None:
        note.source_system = note_update.source_system
    if note_update.source_ref is not None:
        note.source_ref = note_update.source_ref
    note.updated_at = datetime.utcnow()
    note.updated_by = updated_by
    db.add(note)
    db.commit()
    db.refresh(note)
    delta = CompanyDelta(notes_updated=[_note_snapshot(note)])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return note


def delete_company_note(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    note_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    company = get_company(db, tenant_id=tenant_id, company_id=company_id)
    note = next((n for n in company.notes if n.id == note_id), None)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    delta = CompanyDelta(notes_deleted=[note.id])
    CompanyProducer.send_company_updated(
        tenant_id=tenant_id,
        changes=delta,
        payload=_company_snapshot(company),
    )
    return None


# ---------------------------------------------------------------------------
# CompanyRelationship operations
# ---------------------------------------------------------------------------


def add_company_relationship(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    from_company_id: uuid.UUID,
    rel_in: CompanyRelationshipCreateRequest,
    updated_by: Optional[str] = None,
) -> CompanyRelationship:
    company = get_company(db, tenant_id=tenant_id, company_id=from_company_id)
    rel = CompanyRelationship(
        tenant_id=tenant_id,
        from_company_id=company.id,
        to_company_id=rel_in.to_company_id,
        from_role=rel_in.from_role,
        to_role=rel_in.to_role,
        is_active=rel_in.is_active if rel_in.is_active is not None else True,
        start_date=rel_in.start_date,
        end_date=rel_in.end_date,
        notes=rel_in.notes,
        created_by=updated_by,
        updated_by=updated_by,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    # Emit relationship created event
    CompanyRelationshipProducer.send_relationship_created(
        tenant_id=tenant_id,
        from_company_id=from_company_id,
        to_company_id=rel_in.to_company_id,
        payload=_relationship_snapshot(rel),
    )
    return rel


def update_company_relationship(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    from_company_id: uuid.UUID,
    relationship_id: uuid.UUID,
    rel_update: CompanyRelationshipUpdateRequest,
    updated_by: Optional[str] = None,
) -> CompanyRelationship:
    rel = (
        db.query(CompanyRelationship)
        .filter(
            CompanyRelationship.tenant_id == tenant_id,
            CompanyRelationship.id == relationship_id,
            CompanyRelationship.from_company_id == from_company_id,
        )
        .first()
    )
    if rel is None:
        raise HTTPException(status_code=404, detail="CompanyRelationship not found")
    changes: Dict[str, Any] = {}
    if rel_update.from_role is not None:
        rel.from_role = rel_update.from_role
        changes["from_role"] = rel_update.from_role
    if rel_update.to_role is not None:
        rel.to_role = rel_update.to_role
        changes["to_role"] = rel_update.to_role
    if rel_update.is_active is not None:
        rel.is_active = rel_update.is_active
        changes["is_active"] = rel_update.is_active
    if rel_update.start_date is not None:
        rel.start_date = rel_update.start_date
        changes["start_date"] = rel_update.start_date
    if rel_update.end_date is not None:
        rel.end_date = rel_update.end_date
        changes["end_date"] = rel_update.end_date
    if rel_update.notes is not None:
        rel.notes = rel_update.notes
        changes["notes"] = rel_update.notes
    rel.updated_at = datetime.utcnow()
    rel.updated_by = updated_by
    db.add(rel)
    db.commit()
    db.refresh(rel)
    CompanyRelationshipProducer.send_relationship_updated(
        tenant_id=tenant_id,
        from_company_id=from_company_id,
        to_company_id=rel.to_company_id,
        changes=changes,
        payload=_relationship_snapshot(rel),
    )
    return rel


def delete_company_relationship(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    from_company_id: uuid.UUID,
    relationship_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    rel = (
        db.query(CompanyRelationship)
        .filter(
            CompanyRelationship.tenant_id == tenant_id,
            CompanyRelationship.id == relationship_id,
            CompanyRelationship.from_company_id == from_company_id,
        )
        .first()
    )
    if rel is None:
        raise HTTPException(status_code=404, detail="CompanyRelationship not found")
    to_company_id = rel.to_company_id
    db.delete(rel)
    db.commit()
    CompanyRelationshipProducer.send_relationship_deleted(
        tenant_id=tenant_id,
        from_company_id=from_company_id,
        to_company_id=to_company_id,
    )
    return None


# ---------------------------------------------------------------------------
# Company contacts (ContactCompanyRelationship) operations
# ---------------------------------------------------------------------------


def list_company_contacts(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
) -> List[ContactCompanyRelationship]:
    return (
        db.query(ContactCompanyRelationship)
        .filter(
            ContactCompanyRelationship.tenant_id == tenant_id,
            ContactCompanyRelationship.company_id == company_id,
        )
        .all()
    )


def add_company_contact(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    request: CompanyContactRelationshipCreateRequest,
    updated_by: Optional[str] = None,
) -> ContactCompanyRelationship:
    # Ensure company exists
    _ = get_company(db, tenant_id=tenant_id, company_id=company_id)
    rel = ContactCompanyRelationship(
        tenant_id=tenant_id,
        contact_id=request.contact_id,
        company_id=company_id,
        relationship_type=request.relationship_type,
        department=request.department,
        job_title=request.job_title,
        work_email=request.work_email,
        work_phone_raw=request.work_phone_raw,
        work_phone_e164=request.work_phone_e164,
        work_phone_ext=request.work_phone_ext,
        is_primary=request.is_primary or False,
        start_date=request.start_date,
        end_date=request.end_date,
        is_active=request.is_active if request.is_active is not None else True,
        created_by=updated_by,
        updated_by=updated_by,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    # Emit event via contact company relationship producer
    ContactCompanyRelationshipProducer.send_relationship_created(
        tenant_id=tenant_id,
        contact_id=request.contact_id,
        company_id=company_id,
        payload=_contact_rel_snapshot(rel),
    )
    return rel


def update_company_contact(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    contact_id: uuid.UUID,
    request: CompanyContactRelationshipUpdateRequest,
    updated_by: Optional[str] = None,
) -> ContactCompanyRelationship:
    rel = (
        db.query(ContactCompanyRelationship)
        .filter(
            ContactCompanyRelationship.tenant_id == tenant_id,
            ContactCompanyRelationship.company_id == company_id,
            ContactCompanyRelationship.contact_id == contact_id,
        )
        .first()
    )
    if rel is None:
        raise HTTPException(status_code=404, detail="Contact relationship not found")
    changes: Dict[str, Any] = {}
    if request.relationship_type is not None:
        rel.relationship_type = request.relationship_type
        changes["relationship_type"] = request.relationship_type
    if request.department is not None:
        rel.department = request.department
        changes["department"] = request.department
    if request.job_title is not None:
        rel.job_title = request.job_title
        changes["job_title"] = request.job_title
    if request.work_email is not None:
        rel.work_email = request.work_email
        changes["work_email"] = request.work_email
    if request.work_phone_raw is not None:
        rel.work_phone_raw = request.work_phone_raw
        changes["work_phone_raw"] = request.work_phone_raw
    if request.work_phone_e164 is not None:
        rel.work_phone_e164 = request.work_phone_e164
        changes["work_phone_e164"] = request.work_phone_e164
    if request.work_phone_ext is not None:
        rel.work_phone_ext = request.work_phone_ext
        changes["work_phone_ext"] = request.work_phone_ext
    if request.is_primary is not None:
        rel.is_primary = request.is_primary
        changes["is_primary"] = request.is_primary
    if request.start_date is not None:
        rel.start_date = request.start_date
        changes["start_date"] = request.start_date
    if request.end_date is not None:
        rel.end_date = request.end_date
        changes["end_date"] = request.end_date
    if request.is_active is not None:
        rel.is_active = request.is_active
        changes["is_active"] = request.is_active
    rel.updated_at = datetime.utcnow()
    rel.updated_by = updated_by
    db.add(rel)
    db.commit()
    db.refresh(rel)
    ContactCompanyRelationshipProducer.send_relationship_updated(
        tenant_id=tenant_id,
        contact_id=contact_id,
        company_id=company_id,
        changes=changes,
        payload=_contact_rel_snapshot(rel),
    )
    return rel


def delete_company_contact(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    contact_id: uuid.UUID,
    updated_by: Optional[str] = None,
) -> None:
    rel = (
        db.query(ContactCompanyRelationship)
        .filter(
            ContactCompanyRelationship.tenant_id == tenant_id,
            ContactCompanyRelationship.company_id == company_id,
            ContactCompanyRelationship.contact_id == contact_id,
        )
        .first()
    )
    if rel is None:
        raise HTTPException(status_code=404, detail="Contact relationship not found")
    db.delete(rel)
    db.commit()
    ContactCompanyRelationshipProducer.send_relationship_deleted(
        tenant_id=tenant_id,
        contact_id=contact_id,
        company_id=company_id,
    )
    return None
