"""Data sanitization and ID generation utilities for persistence operations."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4


def ensure_id(prefix: str, id_: str | None) -> str:
    """Generate ID with prefix if not provided."""
    return id_ or f"{prefix}:{uuid4()}"


def is_primitive(x: Any) -> bool:
    """Check if value is a primitive type suitable for direct storage."""
    return isinstance(x, str | int | float | bool) or x is None


def sanitize_value(value: Any) -> Any:
    """Sanitize values for Neo4j storage, converting complex types to JSON strings."""
    if is_primitive(value):
        return value
    if isinstance(value, list):
        if all(is_primitive(i) for i in value):
            return value
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        if not value:
            # Avoid empty Map{} (invalid in Neo4j); store as JSON string
            return json.dumps(value, ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False)
    return str(value)
