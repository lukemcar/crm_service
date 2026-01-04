"""
FastAPI router for Record Watcher tenant endpoints.

Tenant routes expose collection and singleton endpoints for record
watchers owned by a tenant.  All paths embed the tenant identifier in
the URL to enforce isolation.  Collection endpoints are nested under
records (``/tenants/{tenant_id}/records/{record_type}/{record_id}/watchers``)
while singleton endpoints live at
``/tenants/{tenant_id}/records/{record_type}/{record_id}/watchers/{principal_type}/{principal_id}``.

Mutating operations accept an ``X‑User‑Id`` header to capture audit
information.  Business logic is delegated to the service layer
``record_watcher_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from fastapi import Query
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
)
def list_watchers(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    record_type: str = Path(..., description="Type of the record (e.g., CONTACT, COMPANY, DEAL)"),
    record_id: UUID = Path(..., description="Identifier of the record"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of watchers to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of watchers to skip"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[RecordWatcherRead]:
    """List watchers for a record (tenant context).

    Does not verify that the record exists; the caller should ensure the
    record belongs to the tenant.  Pagination parameters are optional.
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
)
def create_watcher(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    record_type: str = Path(..., description="Type of the record"),
    record_id: UUID = Path(..., description="Identifier of the record"),
    watcher_in: RecordWatcherCreate,
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> RecordWatcherRead:
    """Create a watcher (tenant context).

    The ``tenant_id``, ``record_type`` and ``record_id`` in the request body
    are ignored and overwritten with the path parameters to prevent cross‑tenant
    or cross‑record associations.
    """
    watcher_data = watcher_in.model_copy(update={
        "tenant_id": tenant_id,
        "record_type": record_type,
        "record_id": record_id,
    })
    created_by_user_id: Optional[UUID] = None
    if x_user_id:
        try:
            created_by_user_id = UUID(x_user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id header")
    watcher = record_watcher_service.service_create_watcher(
        db,
        tenant_id=tenant_id,
        watcher_in=watcher_data,
        created_by_user_id=created_by_user_id,
    )
    return watcher


# ---------------------------------------------------------------------------
# Singleton endpoints: /tenants/{tenant_id}/records/{record_type}/{record_id}/watchers/{principal_type}/{principal_id}
# ---------------------------------------------------------------------------

singleton_router = APIRouter(prefix="/tenants/{tenant_id}/records/{record_type}/{record_id}/watchers")


@singleton_router.delete(
    "/{principal_type}/{principal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_watcher(
    *,
    tenant_id: UUID = Path(..., description="Tenant identifier"),
    record_type: str = Path(..., description="Type of the record"),
    record_id: UUID = Path(..., description="Identifier of the record"),
    principal_type: str = Path(..., description="Type of the principal (USER or GROUP)"),
    principal_id: UUID = Path(..., description="Identifier of the principal"),
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a watcher (tenant context).

    Does not verify that the record belongs to the tenant.  The caller must
    ensure that the referenced record and principal are scoped correctly.
    """
    deleted_by_user_id: Optional[UUID] = None
    if x_user_id:
        try:
            deleted_by_user_id = UUID(x_user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id header")
    record_watcher_service.service_delete_watcher(
        db,
        tenant_id=tenant_id,
        record_type=record_type,
        record_id=record_id,
        principal_type=principal_type,
        principal_id=principal_id,
        deleted_by_user_id=deleted_by_user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Attach sub‑routers to the parent router
router.include_router(collection_router)
router.include_router(singleton_router)
