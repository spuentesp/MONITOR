from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def deep_merge(base: Mapping[str, Any] | None, patch: Mapping[str, Any] | None) -> dict[str, Any]:
    """Recursively merge dict-like structures.
    - Dict vs Dict: merge keys; recurse; patch wins on conflicts.
    - Other types (lists/atoms): patch replaces base.
    """
    out: dict[str, Any] = dict(base or {})
    for k, v in dict(patch or {}).items():
        bv = out.get(k)
        if isinstance(v, dict) and isinstance(bv, dict):
            out[k] = deep_merge(bv, v)
        else:
            out[k] = v
    return out
