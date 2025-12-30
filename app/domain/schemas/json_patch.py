from pydantic import BaseModel
from typing import List, Optional, Any


class JsonPatchOperation(BaseModel):
    """Represents a single JSON Patch operation."""
    op: str  # "add", "replace", or "remove"
    path: str  # JSON Pointer path (e.g., "/preferences/bio")
    value: Optional[Any] = None  # Value to set (not required for "remove" op)

class JsonPatchRequest(BaseModel):
    """Schema for a JSON Patch request containing multiple operations."""
    operations: List[JsonPatchOperation]
