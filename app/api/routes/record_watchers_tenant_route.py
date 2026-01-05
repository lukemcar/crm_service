"""
FastAPI router for Record Watcher tenant endpoints.

Tenant routes expose collection endpoints for watchers owned by
records.  All paths embed the tenant identifier in the URL to
enforce isolation.  Collection endpoints are nested under records
(``/tenants/{tenant_id}/records/{record_type}/{record_id}/watchers``).

Mutating operations accept an ``X‑User`` header to capture audit
information.  Business logic is delegated to the service layer
``record_watcher_service.py``.  Callers should perform validation
of record and principal existence before invoking these endpoints.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.schemas.record_watcher import RecordWatcherCreate, RecordWatcherRead
from app.domain.services import record_watcher_service


# Parent router for tenant record watcher endpoints
router = APIRouter(tags=["record watchers"])

# ---------------------------------------------------------------------------
# Collection endpoints: /tenants/{tenant_id}/records/{record_type}/{record_id}/watchers
# ---------------------------------------------------------------------------

collection_router = APIRouter(prefix="/tenants/{tenant_id}/records/{record_type}/{record_id}/watchers")


@collection_router.get(
    "/",
    response_model=schemas.PaginationEnvelope[RecordWatcherRead],
    name="list_watchers_for_record_tenant",
)
def list_watchers(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    record_type: str = Path(..., description="Type of the record being watched"),
    record_id: UUID = Path(..., description="Identifier of the record being watched"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of watchers to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of watchers to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[RecordWatcherRead]:
    """List watchers for a record (tenant context).

    The caller should ensure the record belongs to the tenant and exists
    before invoking this endpoint.  Pagination is optional.
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


@collection_router.post(
    "/",
    response_model=RecordWatcherRead,
    status_code=status.HTTP_201_CREATED,
    name="create_record_watcher_tenant",
)
def create_watcher(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    record_type: str = Path(..., description="Type of the record being watched"),
    record_id: UUID = Path(..., description="Identifier of the record being watched"),
    watcher_in: RecordWatcherCreate,
    x_user: str = Header(
        ..., alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> RecordWatcherRead:
    """Create a new record watcher under a record (tenant context)."""
    watcher = record_watcher_service.service_create_watcher(
        db,
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        watcher_in=watcher_in,
        created_user_id=x_user,
    )
    return watcher


@collection_router.delete(
    "/{principal_type}/{principal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    name="delete_record_watcher_tenant",
)
def delete_watcher(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    record_type: str = Path(..., description="Type of the record being watched"),
    record_id: UUID = Path(..., description="Identifier of the record being watched"),
    principal_type: str = Path(..., description="Type of the principal"),
    principal_id: UUID = Path(..., description="Identifier of the principal"),
    x_user: Optional[str] = Header(
        None, alias="X-User", description="User performing the operation"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a watcher under a record (tenant context)."""
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


# Attach sub‑router to the parent router
router.include_router(collection_router)