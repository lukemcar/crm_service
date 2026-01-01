"""
Tests for tenant‑scoped knowledge base section endpoints.

These tests verify that the section route handlers call the service layer with
correct parameters, propagate tenant and category identifiers, and use the
`X‑User` header for audit fields on create/update/delete operations.  The
pattern follows other support domain route tests.
"""

from __future__ import annotations

import uuid
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.kb_section import (
    TenantCreateKbSection,
    KbSectionUpdate,
    KbSectionOut,
)
from app.domain.services import kb_section_service
from app.api.routes.kb_sections_tenant_route import (
    list_kb_sections_tenant_endpoint,
    create_kb_section_tenant_endpoint,
    update_kb_section_tenant_endpoint,
    get_kb_section_tenant_endpoint,
    delete_kb_section_tenant_endpoint,
)


class DummySession(Session):
    """Lightweight stand‑in session for tests."""

    pass


def _fake_kb_section_out(
    tenant_id: uuid.UUID,
    section_id: uuid.UUID,
    category_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
    is_active: bool = True,
) -> KbSectionOut:
    return KbSectionOut(
        id=section_id,
        tenant_id=tenant_id,
        kb_category_id=category_id,
        name=name,
        description=description,
        is_active=is_active,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


# ---------------------------------------------------------------------------
# list_kb_sections_tenant_endpoint
# ---------------------------------------------------------------------------


def test_list_kb_sections_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    fake_db = DummySession()
    fake_sections = [
        _fake_kb_section_out(
            tenant_id=tenant_id,
            section_id=uuid.uuid4(),
            category_id=cat_id,
            name="Section 1",
        ),
    ]
    total = len(fake_sections)
    captured_kwargs: dict = {}

    def fake_list(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_sections, total

    monkeypatch.setattr(kb_section_service, "list_kb_sections", fake_list)

    result = list_kb_sections_tenant_endpoint(
        tenant_id=tenant_id,
        kb_category_id=cat_id,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["kb_category_id"] == cat_id
    assert result == [s for s in fake_sections]


# ---------------------------------------------------------------------------
# create_kb_section_tenant_endpoint
# ---------------------------------------------------------------------------


def test_create_kb_section_uses_x_user_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateKbSection(kb_category_id=cat_id, name="New Section", description=None, is_active=True)
    fake_section = _fake_kb_section_out(
        tenant_id=tenant_id,
        section_id=uuid.uuid4(),
        category_id=cat_id,
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    captured_kwargs: dict = {}

    def fake_create(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_section

    monkeypatch.setattr(kb_section_service, "create_kb_section", fake_create)

    result = create_kb_section_tenant_endpoint(
        section_in=payload,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_section


# ---------------------------------------------------------------------------
# update_kb_section_tenant_endpoint
# ---------------------------------------------------------------------------


def test_update_kb_section_uses_x_user_as_updated_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    section_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = KbSectionUpdate(name="Updated", description="Desc", is_active=False)
    fake_section = _fake_kb_section_out(
        tenant_id=tenant_id,
        section_id=section_id,
        category_id=uuid.uuid4(),
        name="Updated",
        description="Desc",
        is_active=False,
    )
    captured_kwargs: dict = {}

    def fake_update(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_section

    monkeypatch.setattr(kb_section_service, "update_kb_section", fake_update)

    result = update_kb_section_tenant_endpoint(
        section_update=update_req,
        tenant_id=tenant_id,
        section_id=section_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["section_id"] == section_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_section


# ---------------------------------------------------------------------------
# get_kb_section_tenant_endpoint
# ---------------------------------------------------------------------------


def test_get_kb_section_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    section_id = uuid.uuid4()
    fake_db = DummySession()
    fake_section = _fake_kb_section_out(
        tenant_id=tenant_id,
        section_id=section_id,
        category_id=uuid.uuid4(),
        name="Section",
    )
    captured_kwargs: dict = {}

    def fake_get(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_section

    monkeypatch.setattr(kb_section_service, "get_kb_section", fake_get)

    result = get_kb_section_tenant_endpoint(
        tenant_id=tenant_id,
        section_id=section_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["section_id"] == section_id
    assert result == fake_section


# ---------------------------------------------------------------------------
# delete_kb_section_tenant_endpoint
# ---------------------------------------------------------------------------


def test_delete_kb_section_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    section_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db: Session, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(kb_section_service, "delete_kb_section", fake_delete)

    result = delete_kb_section_tenant_endpoint(
        tenant_id=tenant_id,
        section_id=section_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["section_id"] == section_id
    assert captured_kwargs["deleted_by"] == "tester"
    assert result is None