from __future__ import annotations

from typing import Any

from .tool_context import ToolContext


def notes_tool(_: ToolContext, text: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
    """Record a non-canonical note (framework-neutral stub)."""
    return {"ok": True, "text": text, "scope": scope or {}}
