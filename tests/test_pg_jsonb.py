"""Sanity checks for PostgreSQL‑specific column types.

This test confirms that JSONB columns defined in the CRM schema are
readable and writable when running against the Postgres test container.
It uses the ``db_session`` fixture directly to execute raw SQL against
the ``lead`` table in the ``dyno_crm`` schema.
"""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy import text


@pytest.mark.postgres
@pytest.mark.liquibase
def test_insert_lead_jsonb(db_session) -> None:
    """Insert and retrieve a row with JSONB data in the lead table."""
    lead_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    lead_data = {"phone_numbers": {"home": "123456"}}

    # Insert a row into the lead table.  Only the id, tenant_id and
    # lead_data are specified; other columns have defaults.
    db_session.execute(
        text(
            "INSERT INTO dyno_crm.lead (id, tenant_id, lead_data) "
            "VALUES (:id, :tenant_id, :lead_data)"
        ),
        {"id": lead_id, "tenant_id": tenant_id, "lead_data": lead_data},
    )

    # Query the inserted row back and verify the JSON structure.
    result = db_session.execute(
        text(
            "SELECT lead_data FROM dyno_crm.lead WHERE id = :id"
        ),
        {"id": lead_id},
    ).scalar_one()
    assert result["phone_numbers"]["home"] == "123456"