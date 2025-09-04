"""
Recorder node for LangGraph flows.

This module contains the recorder logic that persists
the final state and changes to the system.
"""

from typing import Any


def recorder_node(state: dict[str, Any], tools: Any) -> dict[str, Any]:
    """
    Recorder node that persists draft and deltas.

    Handles both commit and staging operations based on
    the resolve decision and validation state.
    """
    draft = state.get("draft", "")
    deltas = state.get("deltas", {})
    continuity = state.get("continuity", {})

    # Add continuity data to facts if present
    if continuity and deltas.get("facts"):
        for fact in deltas["facts"]:
            if isinstance(fact, dict):
                # Persist minimal continuity signal
                fact["continuity"] = {
                    k: continuity.get(k)
                    for k in ("drift", "incorrect", "reasons", "constraints", "note")
                    if continuity.get(k) is not None
                }
        deltas["facts"] = deltas["facts"]

    # Respect resolve decision: if agent advises against commit or validations not ok, stage only
    decision = state.get("resolve_decision") or {}
    agent_commit = bool(decision.get("commit")) if isinstance(decision, dict) else False
    validations = state.get("validation") or {}
    validations_ok = bool(validations.get("ok", True))

    # If autopilot, only allow direct commit when agent approves and validations are ok
    ctx = tools["ctx"]
    allow_commit = (not getattr(ctx, "dry_run", True)) and agent_commit and validations_ok

    if allow_commit:
        commit = tools["recorder_tool"](ctx, draft=draft, deltas=deltas)
    else:
        # Build a temporary dry-run ctx for staging
        from core.engine.context_utils import as_dry_run

        stage_ctx = as_dry_run(ctx, True)
        commit = tools["recorder_tool"](stage_ctx, draft=draft, deltas=deltas)

    return {**state, "commit": commit}
