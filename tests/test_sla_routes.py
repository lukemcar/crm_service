from __future__ import annotations

import uuid
from typing import Optional, List

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.sla_policy import (
    TenantCreateSlaPolicy,
    AdminCreateSlaPolicy,
    SlaPolicyUpdate,
    SlaPolicyOut,
)
from app.domain.schemas.sla_target import (
    TenantCreateSlaTarget,
    AdminCreateSlaTarget,
    SlaTargetUpdate,
    SlaTargetOut,
)
from app.domain.services import sla_policy_service, sla_target_service

from app.api.routes.sla_policies_tenant_route import (
    list_sla_policies_endpoint as tenant_list_policies,
    create_sla_policy_endpoint as tenant_create_policy,
    update_sla_policy_endpoint as tenant_update_policy,
    get_sla_policy_endpoint as tenant_get_policy,
    delete_sla_policy_endpoint as tenant_delete_policy,
)
from app.api.routes.sla_policies_admin_route import (
    list_sla_policies_admin as admin_list_policies,
    create_sla_policy_admin as admin_create_policy,
    update_sla_policy_admin as admin_update_policy,
    get_sla_policy_admin as admin_get_policy,
    delete_sla_policy_admin as admin_delete_policy,
)
from app.api.routes.sla_targets_tenant_route import (
    list_sla_targets_endpoint as tenant_list_targets,
    create_sla_target_endpoint as tenant_create_target,
    update_sla_target_endpoint as tenant_update_target,
    get_sla_target_endpoint as tenant_get_target,
    delete_sla_target_endpoint as tenant_delete_target,
)
from app.api.routes.sla_targets_admin_route import (
    list_sla_targets_admin as admin_list_targets,
    create_sla_target_admin as admin_create_target,
    update_sla_target_admin as admin_update_target,
    get_sla_target_admin as admin_get_target,
    delete_sla_target_admin as admin_delete_target,
)
from app.domain.schemas.common import PaginationEnvelope


class DummySession(Session):
    """Lightweight stand‑in to satisfy type hints without a real DB."""


def _fake_policy_out(
    tenant_id: uuid.UUID,
    policy_id: uuid.UUID,
    name: str,
    is_active: bool = True,
) -> SlaPolicyOut:
    return SlaPolicyOut(
        id=policy_id,
        tenant_id=tenant_id,
        name=name,
        description=None,
        is_active=is_active,
        match_rules=None,
        created_at=None,
        updated_at=None,
        created_by="tester",
        updated_by="tester",
    )


def _fake_target_out(
    tenant_id: uuid.UUID,
    target_id: uuid.UUID,
    policy_id: uuid.UUID,
    priority: str,
) -> SlaTargetOut:
    return SlaTargetOut(
        id=target_id,
        tenant_id=tenant_id,
        sla_policy_id=policy_id,
        priority=priority,
        first_response_minutes=None,
        next_response_minutes=None,
        resolution_minutes=None,
        created_at=None,
        created_by="tester",
    )


# ---------------------------------------------------------------------------
# Tenant SLA policy endpoints
# ---------------------------------------------------------------------------


def test_tenant_list_sla_policies_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_policies = [
        _fake_policy_out(tenant_id=tenant_id, policy_id=uuid.uuid4(), name="Default SLA")
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policies, total

    monkeypatch.setattr(sla_policy_service, "list_sla_policies", fake_list)

    result: PaginationEnvelope[SlaPolicyOut] = tenant_list_policies(
        tenant_id=tenant_id,
        is_active=True,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["is_active"] is True
    assert result.total == total
    assert result.items == fake_policies


def test_tenant_create_sla_policy_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateSlaPolicy(name="New SLA", description="desc", is_active=True)
    fake_policy = _fake_policy_out(
        tenant_id=tenant_id, policy_id=uuid.uuid4(), name=payload.name
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policy

    monkeypatch.setattr(sla_policy_service, "create_sla_policy", fake_create)

    result = tenant_create_policy(
        tenant_id=tenant_id,
        policy_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_policy


def test_tenant_update_sla_policy_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = SlaPolicyUpdate(name="Updated")
    fake_policy = _fake_policy_out(
        tenant_id=tenant_id, policy_id=policy_id, name=update_req.name
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policy

    monkeypatch.setattr(sla_policy_service, "update_sla_policy", fake_update)

    result = tenant_update_policy(
        tenant_id=tenant_id,
        policy_id=policy_id,
        policy_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["policy_id"] == policy_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_policy


def test_tenant_get_sla_policy_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    fake_db = DummySession()
    fake_policy = _fake_policy_out(
        tenant_id=tenant_id, policy_id=policy_id, name="Default"
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policy

    monkeypatch.setattr(sla_policy_service, "get_sla_policy", fake_get)

    result = tenant_get_policy(
        tenant_id=tenant_id,
        policy_id=policy_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["policy_id"] == policy_id
    assert result == fake_policy


def test_tenant_delete_sla_policy_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(sla_policy_service, "delete_sla_policy", fake_delete)

    result = tenant_delete_policy(
        tenant_id=tenant_id,
        policy_id=policy_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["policy_id"] == policy_id
    assert result is None


# ---------------------------------------------------------------------------
# Admin SLA policy endpoints
# ---------------------------------------------------------------------------


def test_admin_list_sla_policies_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = DummySession()
    fake_policies: List[SlaPolicyOut] = [
        _fake_policy_out(tenant_id=uuid.uuid4(), policy_id=uuid.uuid4(), name="SLA")
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policies, total

    monkeypatch.setattr(sla_policy_service, "list_sla_policies", fake_list)

    # call without tenant_id to list all
    result = admin_list_policies(
        tenant_id=None,
        is_active=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] is None
    assert result.total == total
    assert result.items == fake_policies


def test_admin_create_sla_policy_uses_tenant_id_and_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = DummySession()
    payload = AdminCreateSlaPolicy(tenant_id=uuid.uuid4(), name="Admin SLA", description=None, is_active=True)
    fake_policy = _fake_policy_out(tenant_id=payload.tenant_id, policy_id=uuid.uuid4(), name=payload.name)
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policy

    monkeypatch.setattr(sla_policy_service, "create_sla_policy", fake_create)

    result = admin_create_policy(
        policy_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == payload.tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_policy


def test_admin_update_sla_policy_requires_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    policy_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = SlaPolicyUpdate(description="changed")
    fake_policy = _fake_policy_out(tenant_id=tenant_id, policy_id=policy_id, name="changed")
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policy

    monkeypatch.setattr(sla_policy_service, "update_sla_policy", fake_update)

    result = admin_update_policy(
        policy_id=policy_id,
        tenant_id=tenant_id,
        policy_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["policy_id"] == policy_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_policy


def test_admin_get_sla_policy_requires_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    policy_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_policy = _fake_policy_out(
        tenant_id=tenant_id, policy_id=policy_id, name="sla"
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_policy

    monkeypatch.setattr(sla_policy_service, "get_sla_policy", fake_get)

    result = admin_get_policy(
        policy_id=policy_id,
        tenant_id=tenant_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["policy_id"] == policy_id
    assert result == fake_policy


def test_admin_delete_sla_policy_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    policy_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(sla_policy_service, "delete_sla_policy", fake_delete)

    result = admin_delete_policy(
        policy_id=policy_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["policy_id"] == policy_id
    assert result is None


# ---------------------------------------------------------------------------
# Tenant SLA target endpoints
# ---------------------------------------------------------------------------


def test_tenant_list_sla_targets_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    fake_db = DummySession()
    fake_targets = [
        _fake_target_out(tenant_id=tenant_id, target_id=uuid.uuid4(), policy_id=policy_id, priority="low")
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_targets, total

    monkeypatch.setattr(sla_target_service, "list_sla_targets", fake_list)

    result: PaginationEnvelope[SlaTargetOut] = tenant_list_targets(
        tenant_id=tenant_id,
        sla_policy_id=policy_id,
        priority="low",
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["sla_policy_id"] == policy_id
    assert captured_kwargs["priority"] == "low"
    assert result.total == total
    assert result.items == fake_targets


def test_tenant_create_sla_target_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    payload = TenantCreateSlaTarget(sla_policy_id=uuid.uuid4(), priority="high", first_response_minutes=30)
    fake_target = _fake_target_out(
        tenant_id=tenant_id,
        target_id=uuid.uuid4(),
        policy_id=payload.sla_policy_id,
        priority=payload.priority,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_target

    monkeypatch.setattr(sla_target_service, "create_sla_target", fake_create)

    result = tenant_create_target(
        tenant_id=tenant_id,
        target_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_target


def test_tenant_update_sla_target_uses_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    target_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = SlaTargetUpdate(first_response_minutes=15)
    fake_target = _fake_target_out(
        tenant_id=tenant_id,
        target_id=target_id,
        policy_id=uuid.uuid4(),
        priority="low",
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_target

    monkeypatch.setattr(sla_target_service, "update_sla_target", fake_update)

    result = tenant_update_target(
        tenant_id=tenant_id,
        target_id=target_id,
        target_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["target_id"] == target_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_target


def test_tenant_get_sla_target_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    target_id = uuid.uuid4()
    fake_db = DummySession()
    fake_target = _fake_target_out(
        tenant_id=tenant_id, target_id=target_id, policy_id=uuid.uuid4(), priority="normal"
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_target

    monkeypatch.setattr(sla_target_service, "get_sla_target", fake_get)

    result = tenant_get_target(
        tenant_id=tenant_id,
        target_id=target_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["target_id"] == target_id
    assert result == fake_target


def test_tenant_delete_sla_target_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    target_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(sla_target_service, "delete_sla_target", fake_delete)

    result = tenant_delete_target(
        tenant_id=tenant_id,
        target_id=target_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["target_id"] == target_id
    assert result is None


# ---------------------------------------------------------------------------
# Admin SLA target endpoints
# ---------------------------------------------------------------------------


def test_admin_list_sla_targets_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = DummySession()
    fake_targets: List[SlaTargetOut] = [
        _fake_target_out(tenant_id=uuid.uuid4(), target_id=uuid.uuid4(), policy_id=uuid.uuid4(), priority="low")
    ]
    total = 1
    captured_kwargs: dict = {}

    def fake_list(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_targets, total

    monkeypatch.setattr(sla_target_service, "list_sla_targets", fake_list)

    result = admin_list_targets(
        tenant_id=None,
        sla_policy_id=None,
        priority=None,
        limit=None,
        offset=None,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] is None
    assert result.total == total
    assert result.items == fake_targets


def test_admin_create_sla_target_uses_tenant_id_and_x_user(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = DummySession()
    payload = AdminCreateSlaTarget(
        tenant_id=uuid.uuid4(), sla_policy_id=uuid.uuid4(), priority="urgent"
    )
    fake_target = _fake_target_out(
        tenant_id=payload.tenant_id,
        target_id=uuid.uuid4(),
        policy_id=payload.sla_policy_id,
        priority=payload.priority,
    )
    captured_kwargs: dict = {}

    def fake_create(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_target

    monkeypatch.setattr(sla_target_service, "create_sla_target", fake_create)

    result = admin_create_target(
        target_in=payload,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == payload.tenant_id
    assert captured_kwargs["request"] == payload
    assert captured_kwargs["created_by"] == "tester"
    assert result == fake_target


def test_admin_update_sla_target_requires_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    target_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    update_req = SlaTargetUpdate(next_response_minutes=10)
    fake_target = _fake_target_out(
        tenant_id=tenant_id,
        target_id=target_id,
        policy_id=uuid.uuid4(),
        priority="normal",
    )
    captured_kwargs: dict = {}

    def fake_update(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_target

    monkeypatch.setattr(sla_target_service, "update_sla_target", fake_update)

    result = admin_update_target(
        target_id=target_id,
        tenant_id=tenant_id,
        target_update=update_req,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["target_id"] == target_id
    assert captured_kwargs["request"] == update_req
    assert captured_kwargs["updated_by"] == "tester"
    assert result == fake_target


def test_admin_get_sla_target_requires_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    target_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    fake_target = _fake_target_out(
        tenant_id=tenant_id, target_id=target_id, policy_id=uuid.uuid4(), priority="high"
    )
    captured_kwargs: dict = {}

    def fake_get(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return fake_target

    monkeypatch.setattr(sla_target_service, "get_sla_target", fake_get)

    result = admin_get_target(
        target_id=target_id,
        tenant_id=tenant_id,
        db=fake_db,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["target_id"] == target_id
    assert result == fake_target


def test_admin_delete_sla_target_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    target_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    captured_kwargs: dict = {}

    def fake_delete(db, **kwargs):
        captured_kwargs["db"] = db
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(sla_target_service, "delete_sla_target", fake_delete)

    result = admin_delete_target(
        target_id=target_id,
        tenant_id=tenant_id,
        db=fake_db,
        x_user="tester",
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["target_id"] == target_id
    assert result is None
