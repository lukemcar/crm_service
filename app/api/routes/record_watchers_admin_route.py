"""
FastAPI router for Record Watcher admin endpoints.

Administrators can list, create and delete record watchers across tenants.
Collection endpoints are nested under the record path
(``/admin/records/{record_type}/{record_id}/watchers``) and support
optional ``tenant_id`` queries for cross‑tenant filtering.  Singleton
endpoints operate on the composite key identifying a watcher.

For create and delete operations, the ``X‑User`` header is used to
capture audit information.  All business logic is delegated to the
service layer defined in ``record_watcher_service.py``.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain import schemas
from app.domain.schemas.record_watcher import RecordWatcherCreate, RecordWatcherRead
from app.domain.services import record_watcher_service


# Parent router to aggregate collection and singleton sub‑routers
router = APIRouter(tags=["record watchers"])

# ---------------------------------------------------------------------------
# Collection endpoints: /admin/records/{record_type}/{record_id}/watchers
# ---------------------------------------------------------------------------

collection_router = APIRouter(prefix="/admin/records/{record_type}/{record_id}/watchers")


@collection_router.get(
    "/",
    response_model=schemas.PaginationEnvelope[RecordWatcherRead],
)
def list_watchers_for_record(
    *,
    record_type: str = Path(..., description="Type of the record (e.g., CONTACT, COMPANY, DEAL)"),
    record_id: UUID = Path(..., description="Identifier of the record"),
    tenant_id: Optional[UUID] = Query(
        None, description="Tenant identifier for scoping; omit to ignore tenant filtering"
    ),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of watchers to return"),
    offset: Optional[int] = Query(None, ge=0, description="Number of watchers to skip from the beginning"),
    db: Session = Depends(get_db),
) -> schemas.PaginationEnvelope[RecordWatcherRead]:
    """List watchers for a record (admin context).

    If ``tenant_id`` is provided, the record must belong to that tenant or a 404
    error is raised.  Pagination is optional.
    """
    # NOTE: Domain validation (ensuring record belongs to tenant) should occur
    # in a higher-level service.  Here we simply filter by tenant when given.
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
def create_watcher_for_record(
    *,
    record_type: str = Path(..., description="Type of the record"),
    record_id: UUID = Path(..., description="Identifier of the record"),
    tenant_id: UUID = Query(..., description="Tenant identifier for the record"),
    watcher_in: RecordWatcherCreate,
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> RecordWatcherRead:
    """Create a new watcher for a record (admin context).

    The ``tenant_id`` in the request body must match the query parameter.
    The ``record_type`` and ``record_id`` in the body must match the path parameters.
    """
    # Overwrite record_type and record_id to prevent cross‑record associations
    watcher_data = watcher_in.model_copy(update={
        "tenant_id": tenant_id,
        "record_type": record_type,
        "record_id": record_id,
    })
    # Convert x_user_id header to UUID if present
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
# Singleton endpoints: /admin/records/{record_type}/{record_id}/watchers/{principal_type}/{principal_id}
# ---------------------------------------------------------------------------

singleton_router = APIRouter(prefix="/admin/records/{record_type}/{record_id}/watchers")


@singleton_router.delete(
    "/{principal_type}/{principal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_watcher(
    *,
    record_type: str = Path(..., description="Type of the record"),
    record_id: UUID = Path(..., description="Identifier of the record"),
    principal_type: str = Path(..., description="Type of the principal (USER or GROUP)"),
    principal_id: UUID = Path(..., description="Identifier of the principal"),
    tenant_id: UUID = Query(..., description="Tenant identifier"),
    x_user_id: Optional[str] = Header(
        None,
        alias="X-User-Id",
        description="Identifier of the user performing the operation",
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a watcher (admin context).

    The caller must ensure the referenced record and principal belong to the tenant.
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


# Include sub‑routers into the parent router
router.include_router(collection_router)
router.include_router(singleton_router)
