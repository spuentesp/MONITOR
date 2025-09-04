from __future__ import annotations

from typing import Any


def clear_cache_if_present(ctx: Any) -> None:
    """Best-effort read cache clear on context."""
    try:
        cache = getattr(ctx, "read_cache", None)
        if cache is not None:
            cache.clear()
    except Exception:
        pass
