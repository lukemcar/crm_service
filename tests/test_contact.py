"""Tests for the contact API endpoints.

These tests exercise the contact CRUD endpoints using a test database.
They verify that contacts can be created, retrieved, updated and
deleted in the context of a single tenant.  The tests rely on the
``test_client`` fixture defined in ``conftest.py``.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status


@pytest.mark.postgres
@pytest.mark.liquibase
def test_create_and_get_contact(test_client):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        # Provide nested collections matching the API contract.  The
        # ContactPhoneNumberCreateRequest uses ``phone_raw`` as the required
        # field and ContactEmailCreateRequest uses ``email``.
        "phones": [
            {"phone_raw": "123-456-7890"}
        ],
        "emails": [
            {"email": "alice@example.com"}
        ],
    }
    # Create a new contact using the tenant‑scoped route.  User identity is
    # provided via the ``X-User`` header.
    response = test_client.post(
        f"/tenants/{tenant_id}/contacts",
        json=payload,
        headers={"X-User": str(user_id)},
    )
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    assert created["first_name"] == payload["first_name"]
    assert created["last_name"] == payload["last_name"]
    # Validate that the nested email was persisted
    assert created["emails"][0]["email"] == payload["emails"][0]["email"]
    assert created["tenant_id"] == str(tenant_id)
    contact_id = created["id"]
    # Retrieve the contact
    get_resp = test_client.get(
        f"/tenants/{tenant_id}/contacts/{contact_id}"
    )
    assert get_resp.status_code == status.HTTP_200_OK
    retrieved = get_resp.json()
    assert retrieved["id"] == contact_id
    assert retrieved["first_name"] == payload["first_name"]


@pytest.mark.postgres
@pytest.mark.liquibase
def test_update_contact(test_client):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    # Create contact
    payload = {
        "first_name": "Bob",
        "last_name": "Jones",
        "phones": [
            {"phone_raw": "555-555-5555"}
        ],
        "emails": [
            {"email": "bob@example.com"}
        ],
    }
    create_resp = test_client.post(
        f"/tenants/{tenant_id}/contacts",
        json=payload,
        headers={"X-User": str(user_id)},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    contact_id = create_resp.json()["id"]
    # Update contact by replacing the first name via JSON Patch
    patch_request = {
        "operations": [
            {"op": "replace", "path": "/first_name", "value": "Robert"}
        ]
    }
    update_resp = test_client.patch(
        f"/tenants/{tenant_id}/contacts/{contact_id}",
        json=patch_request,
        headers={"X-User": str(user_id)},
    )
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["first_name"] == "Robert"


@pytest.mark.postgres
@pytest.mark.liquibase
def test_delete_contact(test_client):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    payload = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "emails": [
            {"email": "charlie@example.com"}
        ],
    }
    create_resp = test_client.post(
        f"/tenants/{tenant_id}/contacts",
        json=payload,
        headers={"X-User": str(user_id)},
    )
    contact_id = create_resp.json()["id"]
    # Delete contact
    del_resp = test_client.delete(
        f"/tenants/{tenant_id}/contacts/{contact_id}"
    )
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = test_client.get(
        f"/tenants/{tenant_id}/contacts/{contact_id}"
    )
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND