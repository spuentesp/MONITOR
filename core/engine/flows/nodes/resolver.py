"""
Resolver node for LangGraph flows.

This module contains the resolve decider logic that determines
whether to commit or stage changes.
"""

from typing import Any

from core.engine.flows.agent_utils import safe_agent_call


def resolve_decider_node(state: dict[str, Any], tools: Any) -> dict[str, Any]:
    """
    Resolve node with enhanced decision logic.

    Adds more context to the resolve decision to guide whether
    to commit or stage operations.
    """

    # Gather resolution context
    draft = state.get("draft", "")
    actions = state.get("actions", [])
    continuity = state.get("continuity", {})
    validation = state.get("validation", {})

    # Build context for resolution decision
    resolution_context = {
        "draft_length": len(draft) if draft else 0,
        "action_count": len(actions),
        "has_continuity_issues": bool(continuity.get("drift") or continuity.get("incorrect")),
        "validation_ok": validation.get("ok", True),
        "validation_warnings": validation.get("warnings", []),
    }

    # Ask resolve agent for decision
    messages = [
        {
            "role": "user",
            "content": f"Context: {resolution_context}\nShould we commit (true) or stage (false)? Return JSON with 'commit' boolean and optional 'reason'.",
        }
    ]

    decision_raw = safe_agent_call(tools, "resolve", messages, default='{"commit": true}')

    try:
        import json

        decision = json.loads(decision_raw) if isinstance(decision_raw, str) else decision_raw
        if not isinstance(decision, dict):
            decision = {"commit": True, "reason": "Default commit decision"}
    except Exception:
        decision = {"commit": True, "reason": "Failed to parse decision, defaulting to commit"}

    return {**state, "resolve_decision": decision}
