"""
Pydantic models for Lead.

Includes:
- LeadData (validated JSONB structure)
- LeadBase (shared fields)
- CreateLead (create request)
- UpdateLead (patch/update request)
- LeadOut (response)
- LeadListOut (paginated list response, optional)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel, ConfigDict, Field


# -------------------------
# lead_data schema models
# -------------------------


class LeadAddressValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class LeadNoteValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Keep as string to match DB CHECK constraint.
    # If you want strict ISO enforcement, change these to datetime.
    created_at: str = Field(..., min_length=1)
    updated_at: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class LeadData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # { "<type>": "<value>" }
    phone_numbers: Optional[Dict[str, str]] = None

    # { "<type>": "<value>" }
    emails: Optional[Dict[str, str]] = None

    # { "<type>": { ...address fields... } }
    addresses: Optional[Dict[str, LeadAddressValue]] = None

    # { "<type>": "<value>" }   (UPDATED)
    social_profiles: Optional[Dict[str, str]] = None

    # { "<date_label>": { created_at, updated_at, text } }
    notes: Optional[Dict[str, LeadNoteValue]] = None


# -------------------------
# Lead API models
# -------------------------

class LeadBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Optional[str] = Field(default=None, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    source: Optional[str] = Field(default=None, max_length=255)

    lead_data: Optional[LeadData] = None


class CreateLead(LeadBase):
    """
    Create request.

    tenant_id is typically derived from auth context or path param in your API.
    If you want it client-supplied, add tenant_id here.
    """
    pass


class UpdateLead(BaseModel):
    """
    Patch/update request.

    All fields optional. extra=forbid blocks accidental fields.
    """
    model_config = ConfigDict(extra="forbid")

    first_name: Optional[str] = Field(default=None, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    source: Optional[str] = Field(default=None, max_length=255)

    lead_data: Optional[LeadData] = None


class LeadOut(LeadBase):
    """
    Response model.

    Use model_validate(db_obj) with model_config(from_attributes=True) in Pydantic v2.
    """
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID

    created_at: datetime
    updated_at: datetime

    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
__all__ = [
    "LeadData",
    "LeadAddressValue",
    "LeadNoteValue",
    "LeadBase",
    "CreateLead",
    "UpdateLead",
    "LeadOut",
]
