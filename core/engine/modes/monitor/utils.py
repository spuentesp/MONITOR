"""Monitor mode utilities and helper functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.engine.tools import ToolContext, recorder_tool

from ..state import GraphState

if TYPE_CHECKING:
    pass


def commit_deltas(ctx: ToolContext | None, deltas: dict[str, Any]) -> dict[str, Any]:
    """Commit deltas using the recorder tool."""
    if not ctx:
        return {"mode": "noop", "reason": "no_tool_context"}
    draft = deltas.get("_draft", "")
    return recorder_tool(
        ctx, draft=draft, deltas={k: v for k, v in deltas.items() if k != "_draft"}
    )


def auto_flush_if_needed(ctx: ToolContext | None, reason: str) -> dict[str, Any] | None:
    """If running in copilot (dry_run), flush staged changes at safe boundaries.

    This persists via the staging store regardless of ctx.dry_run, which is intentional for
    boundary commits like end_scene. In autopilot (dry_run=False), writes are already persisted.
    """
    try:
        if ctx and getattr(ctx, "dry_run", True):
            # Lazy import to avoid any circulars at module import time
            from core.engine.orchestrator import flush_staging

            return flush_staging(ctx)  # type: ignore[arg-type]
    except Exception:
        return {"ok": False, "error": "auto_flush_failed"}
    return None


def get_wizard_state(state: GraphState) -> dict[str, Any]:
    """Get the current wizard state from the GraphState."""
    return (state.get("meta") or {}).get("wizard") or {}


def update_wizard_state(state: GraphState, wizard_data: dict[str, Any]) -> None:
    """Update the wizard state in the GraphState."""
    meta = state.get("meta") or {}
    meta["wizard"] = wizard_data
    state["meta"] = meta


def clear_wizard_state(state: GraphState) -> None:
    """Clear the wizard state from the GraphState."""
    meta = state.get("meta") or {}
    meta.pop("wizard", None)
    state["meta"] = meta
