"""Tests for the contact API endpoints.

These tests exercise the contact CRUD endpoints using an in‑memory
SQLite database.  They verify that contacts can be created,
retrieved, patched via JSON Patch and deleted within the context of
a single tenant.  The tests rely on the ``test_client`` fixture
defined in ``conftest.py``.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status


def test_create_and_get_contact(test_client):
    """Create a contact and retrieve it via the tenant API."""
    tenant_id = uuid.uuid4()
    # Use a simple payload; phones/emails are optional lists and can be omitted
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
    }
    # Create a new contact
    resp = test_client.post(
        f"/tenants/{tenant_id}/contacts",
        json=payload,
        headers={"X-User": "test-user"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    created = resp.json()
    assert created["first_name"] == payload["first_name"]
    assert created["last_name"] == payload["last_name"]
    assert created["tenant_id"] == str(tenant_id)
    contact_id = created["id"]
    # Retrieve the contact
    get_resp = test_client.get(f"/tenants/{tenant_id}/contacts/{contact_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    retrieved = get_resp.json()
    assert retrieved["id"] == contact_id
    assert retrieved["first_name"] == payload["first_name"]


def test_patch_contact(test_client):
    """Update a contact's first name using JSON Patch."""
    tenant_id = uuid.uuid4()
    # Create a contact
    create_resp = test_client.post(
        f"/tenants/{tenant_id}/contacts",
        json={"first_name": "Bob", "last_name": "Jones"},
        headers={"X-User": "tester"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    contact_id = create_resp.json()["id"]
    # JSON Patch payload: replace first_name
    patch_payload = {
        "operations": [
            {"op": "replace", "path": "/first_name", "value": "Robert"},
        ]
    }
    update_resp = test_client.patch(
        f"/tenants/{tenant_id}/contacts/{contact_id}",
        json=patch_payload,
        headers={"X-User": "tester"},
    )
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["first_name"] == "Robert"


def test_delete_contact(test_client):
    """Delete a contact and ensure it cannot be retrieved."""
    tenant_id = uuid.uuid4()
    # Create contact
    create_resp = test_client.post(
        f"/tenants/{tenant_id}/contacts",
        json={"first_name": "Charlie", "last_name": "Brown"},
        headers={"X-User": "tester"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    contact_id = create_resp.json()["id"]
    # Delete contact
    del_resp = test_client.delete(f"/tenants/{tenant_id}/contacts/{contact_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = test_client.get(f"/tenants/{tenant_id}/contacts/{contact_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND