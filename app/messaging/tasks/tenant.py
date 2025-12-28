"""Consumers for Dyno Tenant Management Service events.

This module defines placeholder handlers for events emitted by the
Tenant Management Service.  The CRM uses these events to mirror the
platform's tenant structure (tenants, users, roles, groups and
their assignments).  Real implementations should upsert
projection tables in the CRM database and update cached role/group
memberships.  For now, the handlers simply log the incoming event
data.

The routing keys correspond to object types and actions as
documented in the Tenant Service Integration Guide, such as
``tenant_mngr_srv.tenant.created`` for new tenants and
``tenant_mngr_srv.tenant_user.updated`` when a membership is
modified.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

import json


def process_tenant_created(envelope: Dict[str, Any]) -> None:
    """Handle a tenant.created event.

    Args:
        envelope: The event envelope as a dictionary.
    """
    data = envelope.get("data", {})
    print(f"[TENANT] Tenant created: {json.dumps(data, default=str)}")


def process_tenant_updated(envelope: Dict[str, Any]) -> None:
    """Handle a tenant.updated event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Tenant updated: {json.dumps(data, default=str)}")


def process_tenant_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a tenant.deleted event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Tenant deleted: {json.dumps(data, default=str)}")


def process_tenant_user_created(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_user.created event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Tenant user created: {json.dumps(data, default=str)}")


def process_tenant_user_updated(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_user.updated event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Tenant user updated: {json.dumps(data, default=str)}")


def process_tenant_user_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_user.deleted event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Tenant user deleted: {json.dumps(data, default=str)}")


def process_role_created(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_role.created event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Role created: {json.dumps(data, default=str)}")


def process_role_updated(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_role.updated event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Role updated: {json.dumps(data, default=str)}")


def process_role_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_role.deleted event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Role deleted: {json.dumps(data, default=str)}")


def process_group_created(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_group.created event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Group created: {json.dumps(data, default=str)}")


def process_group_updated(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_group.updated event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Group updated: {json.dumps(data, default=str)}")


def process_group_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_group.deleted event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Group deleted: {json.dumps(data, default=str)}")


def process_role_assignment_created(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_role_assignment.created event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Role assignment created: {json.dumps(data, default=str)}")


def process_role_assignment_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_role_assignment.deleted event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Role assignment deleted: {json.dumps(data, default=str)}")


def process_group_assignment_created(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_group_assignment.created event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Group assignment created: {json.dumps(data, default=str)}")


def process_group_assignment_deleted(envelope: Dict[str, Any]) -> None:
    """Handle a tenant_group_assignment.deleted event."""
    data = envelope.get("data", {})
    print(f"[TENANT] Group assignment deleted: {json.dumps(data, default=str)}")


def process_unknown(envelope: Dict[str, Any]) -> None:
    """Fallback handler for unrecognised tenant events."""
    print(f"[TENANT] Unhandled event_type={envelope.get('event_type')}")


# Mapping of tenant event types to handler functions.  Extend this
# dictionary to support new events as documented in the Tenant
# Service Integration Guide.
TENANT_EVENT_HANDLERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "tenant_mngr_srv.tenant.created": process_tenant_created,
    "tenant_mngr_srv.tenant.updated": process_tenant_updated,
    "tenant_mngr_srv.tenant.deleted": process_tenant_deleted,
    "tenant_mngr_srv.tenant_user.created": process_tenant_user_created,
    "tenant_mngr_srv.tenant_user.updated": process_tenant_user_updated,
    "tenant_mngr_srv.tenant_user.deleted": process_tenant_user_deleted,
    "tenant_mngr_srv.tenant_role.created": process_role_created,
    "tenant_mngr_srv.tenant_role.updated": process_role_updated,
    "tenant_mngr_srv.tenant_role.deleted": process_role_deleted,
    "tenant_mngr_srv.tenant_group.created": process_group_created,
    "tenant_mngr_srv.tenant_group.updated": process_group_updated,
    "tenant_mngr_srv.tenant_group.deleted": process_group_deleted,
    "tenant_mngr_srv.tenant_role_assignment.created": process_role_assignment_created,
    "tenant_mngr_srv.tenant_role_assignment.deleted": process_role_assignment_deleted,
    "tenant_mngr_srv.tenant_group_assignment.created": process_group_assignment_created,
    "tenant_mngr_srv.tenant_group_assignment.deleted": process_group_assignment_deleted,
}


def consume_tenant_event(envelope: Dict[str, Any]) -> None:
    """Route a tenant event to the appropriate handler.

    Args:
        envelope: The deserialised event envelope from the Tenant service.
    """
    event_type = envelope.get("event_type")
    handler = TENANT_EVENT_HANDLERS.get(event_type, process_unknown)
    handler(envelope)