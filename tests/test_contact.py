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


def test_create_and_get_contact(test_client):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "phone": "123-456-7890",
    }
    # Create a new contact
    response = test_client.post(
        "/contacts/",
        params={"tenant_id": str(tenant_id), "user_id": str(user_id)},
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    assert created["first_name"] == payload["first_name"]
    assert created["last_name"] == payload["last_name"]
    assert created["email"] == payload["email"]
    assert created["tenant_id"] == str(tenant_id)
    contact_id = created["id"]
    # Retrieve the contact
    get_resp = test_client.get(
        f"/contacts/{contact_id}", params={"tenant_id": str(tenant_id)}
    )
    assert get_resp.status_code == status.HTTP_200_OK
    retrieved = get_resp.json()
    assert retrieved["id"] == contact_id
    assert retrieved["first_name"] == payload["first_name"]


def test_update_contact(test_client):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    # Create contact
    payload = {
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob@example.com",
        "phone": "555-555-5555",
    }
    create_resp = test_client.post(
        "/contacts/",
        params={"tenant_id": str(tenant_id), "user_id": str(user_id)},
        json=payload,
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    contact_id = create_resp.json()["id"]
    # Update contact
    update_payload = {"first_name": "Robert"}
    update_resp = test_client.patch(
        f"/contacts/{contact_id}",
        params={"tenant_id": str(tenant_id), "user_id": str(user_id)},
        json=update_payload,
    )
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["first_name"] == "Robert"


def test_delete_contact(test_client):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    payload = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@example.com",
    }
    create_resp = test_client.post(
        "/contacts/",
        params={"tenant_id": str(tenant_id), "user_id": str(user_id)},
        json=payload,
    )
    contact_id = create_resp.json()["id"]
    # Delete contact
    del_resp = test_client.delete(
        f"/contacts/{contact_id}", params={"tenant_id": str(tenant_id)}
    )
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = test_client.get(
        f"/contacts/{contact_id}", params={"tenant_id": str(tenant_id)}
    )
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND