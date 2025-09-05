"""Generic facade pattern for dependency injection."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

P = TypeVar("P", bound=Protocol)


class GenericFacade:
    """Generic facade that forwards method calls to an underlying implementation.

    This allows any object to be adapted to implement a protocol interface
    through delegation, enabling dependency injection while maintaining
    type safety.
    """

    def __init__(self, impl: Any):
        self._impl = impl

    def __getattr__(self, name: str) -> Any:
        """Forward all method calls to the underlying implementation."""
        return getattr(self._impl, name)
