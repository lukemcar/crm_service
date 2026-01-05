"""
FastAPI router for Record Watcher admin endpoints.

Administrators can list, create and delete record watchers across
tenants.  Collection endpoints are nested under record and principal
paths.  A record watcher links a principal (user or group) to a
record (contact, company, deal, etc.).  These endpoints rely on the
service layer defined in ``record_watcher_service.py`` and do not
perform tenant or record existence validation; callers should ensure
the referenced resources are valid.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Response, status, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.schemas.record_watcher import RecordWatcherCreate, RecordWatcherRead
from app.domain.services import record_watcher_service


# Parent router for record watcher endpoints
router = APIRouter(tags=["record watchers"])

# ---------------------------------------------------------------------------
# Record‑scoped endpoints: /admin/records/{record_type}/{record_id}/watchers
# ---------------------------------------------------------------------------

record_router = APIRouter(prefix="/admin/records/{record_type}/{record_id}/watchers")


@record_router.get(
    "/",
    response_model=schemas.PaginationEnvelope[RecordWatcherRead],
    name="list_watchers_for_record_admin",
)
def list_watchers_for_record(
    *,
    record_type: str = Path(..., description="Type of the record being watched"),
    record_id: UUID = Path(..., description="Identifier of the record being watched"),
    tenant_id: UUID = Query(..., description="Tenant identifier for scoping"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of watchers to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of watchers to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[RecordWatcherRead]:
    """List record watchers for a specific record (admin context).

    The caller should validate that the record belongs to the tenant before
    invoking this endpoint.  Pagination is optional.
    """
    items, total = record_watcher_service.service_list_watchers_by_record(
        db,
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[RecordWatcherRead](
        items=items, total=total, limit=limit, offset=offset
    )


@record_router.post(
    "/",
    response_model=RecordWatcherRead,
    status_code=status.HTTP_201_CREATED,
    name="create_record_watcher_admin",
)
def create_watcher_for_record(
    *,
    record_type: str = Path(..., description="Type of the record being watched"),
    record_id: UUID = Path(..., description="Identifier of the record being watched"),
    tenant_id: UUID = Query(..., description="Tenant identifier for scoping"),
    watcher_in: RecordWatcherCreate,
    x_user: str = Header(
        ..., alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> RecordWatcherRead:
    """Create a new record watcher for a record (admin context).

    The ``record_type`` and ``record_id`` path parameters override the
    corresponding fields in the request body to prevent cross‑record
    subscriptions.
    """
    watcher = record_watcher_service.service_create_watcher(
        db,
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        watcher_in=watcher_in,
        created_user_id=x_user,
    )
    return watcher


@record_router.delete(
    "/{principal_type}/{principal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    name="delete_record_watcher_admin",
)
def delete_watcher_for_record(
    *,
    record_type: str = Path(..., description="Type of the record being watched"),
    record_id: UUID = Path(..., description="Identifier of the record being watched"),
    principal_type: str = Path(..., description="Type of the principal"),
    principal_id: UUID = Path(..., description="Identifier of the principal"),
    tenant_id: UUID = Query(..., description="Tenant identifier for scoping"),
    x_user: Optional[str] = Header(
        None, alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a record watcher for a record (admin context)."""
    record_watcher_service.service_delete_watcher(
        db,
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        deleted_user_id=x_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Principal‑scoped endpoints: /admin/principals/{principal_type}/{principal_id}/watchers
# ---------------------------------------------------------------------------

principal_router = APIRouter(prefix="/admin/principals/{principal_type}/{principal_id}/watchers")


@principal_router.get(
    "/",
    response_model=schemas.PaginationEnvelope[RecordWatcherRead],
    name="list_watchers_for_principal_admin",
)
def list_watchers_for_principal(
    *,
    principal_type: str = Path(..., description="Type of the principal"),
    principal_id: UUID = Path(..., description="Identifier of the principal"),
    tenant_id: UUID = Query(..., description="Tenant identifier for scoping"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of watchers to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of watchers to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[RecordWatcherRead]:
    """List record watchers for a principal (admin context)."""
    items, total = record_watcher_service.service_list_watchers_by_principal(
        db,
        tenant_id=tenant_id,
        principal_type=principal_type,
        principal_id=principal_id,
        limit=limit,
        offset=offset,
    )
    return schemas.PaginationEnvelope[RecordWatcherRead](
        items=items, total=total, limit=limit, offset=offset
    )


# Include sub‑routers into the parent router
router.include_router(record_router)
router.include_router(principal_router)