"""
Cache context managing read-through cache and staging operations.

Handles caching layer responsibilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CacheContext:
    """Manages caching and staging operations."""

    read_cache: Any | None = None
    """Read-through cache for query optimization."""

    staging: Any | None = None
    """Staging store for uncommitted changes."""

    def has_caching(self) -> bool:
        """Check if caching is available."""
        return self.read_cache is not None

    def has_staging(self) -> bool:
        """Check if staging is available."""
        return self.staging is not None
