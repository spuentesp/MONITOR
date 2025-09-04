from __future__ import annotations

from typing import Any, Tuple

from core.engine.resolve_tool import resolve_commit_tool
from core.engine.context_utils import as_dry_run


def normalize_validations(v: dict | None) -> dict[str, Any]:
    v = v or {}
    return {
        "ok": bool(v.get("ok", True)),
        "warnings": v.get("warnings") or [],
        "errors": v.get("errors") or [],
    }


def decide_commit(llm: Any, deltas: dict[str, Any], validations: dict | None, mode: str, hints: dict | None = None) -> tuple[dict[str, Any], bool]:
    """Run resolve agent and return (decision, allow_commit).

    allow_commit is True only if mode==autopilot and agent approves and validations ok.
    """
    val = normalize_validations(validations)
    decision = resolve_commit_tool(
        {
            "llm": llm,
            "deltas": deltas,
            "validations": val,
            "mode": mode,
            "hints": hints or {},
        }
    )
    agent_commit = bool(decision.get("commit"))
    allow_commit = bool((mode == "autopilot") and agent_commit and val.get("ok", True))
    return decision, allow_commit


def stage_or_commit(ctx: Any, *, llm: Any, deltas: dict[str, Any], validations: dict | None, mode: str, hints: dict | None = None) -> dict[str, Any]:
    """Unified path to either commit immediately or stage (dry-run) based on resolve decision."""
    from core.engine.tools import recorder_tool

    decision, allow = decide_commit(llm, deltas, validations, mode, hints)
    if allow and not getattr(ctx, "dry_run", True):
        return {
            "decision": decision,
            "commit": recorder_tool(ctx, draft="", deltas=deltas),
        }
    # Stage in dry-run context for traceability
    stage_ctx = as_dry_run(ctx, True)
    return {
        "decision": decision,
        "commit": recorder_tool(stage_ctx, draft="", deltas=deltas),
    }
