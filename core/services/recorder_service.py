from __future__ import annotations

from typing import Any

from core.ports.storage import RecorderWritePort


class RecorderServiceFacade(RecorderWritePort):
    """Thin facade that forwards to an underlying RecorderService-like object."""

    def __init__(self, impl: Any):
        self._impl = impl

    def __getattr__(self, name: str) -> Any:
        return getattr(self._impl, name)

    def commit_deltas(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        return self._impl.commit_deltas(**kwargs)
