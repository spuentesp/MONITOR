"""
Database context managing query and recording operations.

Handles the data persistence layer responsibilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DatabaseContext:
    """Manages database connections and operations."""

    query_service: Any
    """Public read facade for the graph (safe to call)."""

    recorder: Any | None = None
    """Recording service for write operations."""

    dry_run: bool = True
    """If True, Recorder won't persist; returns a plan/diff instead."""

    def is_read_only(self) -> bool:
        """Check if this context is in read-only mode."""
        return self.dry_run or self.recorder is None
