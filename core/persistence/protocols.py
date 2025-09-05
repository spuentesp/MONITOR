"""
Type protocols for persistence layer mixins.

These protocols define the interface contracts that mixins expect
from their base classes, enabling proper type checking with multiple inheritance.
"""

from __future__ import annotations

from typing import Any, Protocol


class RepoProtocol(Protocol):
    """Protocol for repository-like objects."""

    def run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a query with parameters and return results."""
        ...


class BrancherProtocol(Protocol):
    """Protocol for brancher base functionality."""

    repo: RepoProtocol

    def _check_source_and_target(
        self, source_universe_id: str, new_universe_id: str, force: bool
    ) -> None:
        """Check source exists and target constraints."""
        ...

    @staticmethod
    def _first_count(rows: list[dict[str, Any]] | list[Any]) -> int:
        """Extract count from first row."""
        ...


class ProjectorProtocol(Protocol):
    """Protocol for projector base functionality."""

    repo: RepoProtocol

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        """Sanitize value for storage."""
        ...

    @staticmethod
    def _is_primitive(x: Any) -> bool:
        """Check if value is primitive type."""
        ...
