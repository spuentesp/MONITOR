"""
AutoCommit context managing background commit operations.

Handles async auto-commit agent wiring responsibilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AutoCommitContext:
    """Manages auto-commit operations and background workers."""

    enabled: bool = False
    """Whether auto-commit is enabled."""

    queue: Any | None = None
    """Queue for auto-commit operations (e.g., queue.Queue)."""

    worker: Any | None = None
    """Background thread/worker handle."""

    idempotency: set[str] | None = None
    """Simple in-memory idempotency set shared with the worker."""

    def is_active(self) -> bool:
        """Check if auto-commit is active and ready."""
        return self.enabled and self.queue is not None and self.worker is not None

    def has_idempotency_protection(self) -> bool:
        """Check if idempotency protection is available."""
        return self.idempotency is not None
