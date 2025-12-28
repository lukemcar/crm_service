"""
Event message schemas for company lifecycle events.

These models define the structure of messages emitted when company
records are created, updated or deleted.  Each message includes the
``tenant_id`` and a payload snapshot of the company state.  Update
events also include a ``changes`` dictionary describing the fields
that changed.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class CompanyBaseMessage(BaseModel):
    """Base fields common to all company events."""

    tenant_id: UUID


class CompanyCreatedMessage(CompanyBaseMessage):
    """Event emitted when a company is created."""

    payload: Dict[str, Any]


class CompanyUpdatedMessage(CompanyBaseMessage):
    """Event emitted when a company is updated."""

    changes: Dict[str, Any]
    payload: Dict[str, Any]


class CompanyDeletedMessage(CompanyBaseMessage):
    """Event emitted when a company is deleted."""

    deleted_dt: Optional[str] = None
