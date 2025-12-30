"""Tests for the company API endpoints.

These tests exercise the company CRUD endpoints using an in-memory
SQLite database.  They verify that companies can be created,
retrieved, patched via JSON Patch and deleted within the context of
a single tenant.  The tests rely on the ``test_client`` fixture
defined in ``conftest.py``.
"""

from __future__ import annotations

import uuid

from fastapi import status


def test_create_and_get_company(test_client) -> None:
    """Create a company and retrieve it via the tenant API."""
    tenant_id = uuid.uuid4()
    payload = {
        "name": "ACME Corp",
        "website": "acme.com",
    }
    resp = test_client.post(
        f"/tenants/{tenant_id}/companies",
        json=payload,
        headers={"X-User": "tester"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    created = resp.json()
    assert created["name"] == payload["name"]
    assert created["website"] == payload["website"]
    assert created["tenant_id"] == str(tenant_id)
    company_id = created["id"]
    # Retrieve
    get_resp = test_client.get(f"/tenants/{tenant_id}/companies/{company_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    retrieved = get_resp.json()
    assert retrieved["id"] == company_id
    assert retrieved["name"] == payload["name"]


def test_patch_company(test_client) -> None:
    """Update a company's name using JSON Patch."""
    tenant_id = uuid.uuid4()
    create_resp = test_client.post(
        f"/tenants/{tenant_id}/companies",
        json={"name": "Old Name"},
        headers={"X-User": "tester"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    company_id = create_resp.json()["id"]
    patch_payload = {
        "operations": [
            {"op": "replace", "path": "/name", "value": "New Name"},
        ]
    }
    patch_resp = test_client.patch(
        f"/tenants/{tenant_id}/companies/{company_id}",
        json=patch_payload,
        headers={"X-User": "tester"},
    )
    assert patch_resp.status_code == status.HTTP_200_OK
    updated = patch_resp.json()
    assert updated["name"] == "New Name"


def test_delete_company(test_client) -> None:
    """Delete a company and confirm it cannot be retrieved."""
    tenant_id = uuid.uuid4()
    create_resp = test_client.post(
        f"/tenants/{tenant_id}/companies",
        json={"name": "Delete Me"},
        headers={"X-User": "tester"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    company_id = create_resp.json()["id"]
    del_resp = test_client.delete(f"/tenants/{tenant_id}/companies/{company_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    # Attempt to retrieve
    get_resp = test_client.get(f"/tenants/{tenant_id}/companies/{company_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND
