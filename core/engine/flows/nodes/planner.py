"""
Planner node for LangGraph flows.

This module contains the planner node logic that decides
what actions to take based on intent and context.
"""

import json
from typing import Any

from core.engine.flow_utils import tool_schema as flow_tool_schema
from core.engine.flows.agent_utils import safe_agent_call


def _tool_schema() -> list[dict[str, Any]]:
    return flow_tool_schema()


def planner_node(state: dict[str, Any], tools: Any) -> dict[str, Any]:
    """Agentic planner: always request a JSON list of actions; empty list means no-ops.

    The planner decides if/what to do given intent and context.
    """

    # Provide richer but compact context: IDs and librarian/evidence summary if available
    compact_ctx = {
        k: state.get(k)
        for k in ("scene_id", "story_id", "universe_id", "tags")
        if state.get(k) is not None
    }
    if state.get("evidence_summary"):
        compact_ctx["evidence_summary"] = state.get("evidence_summary")

    plan = safe_agent_call(
        tools,
        "planner",
        [
            {
                "role": "user",
                "content": f"Intent: {state.get('intent')}\nContext: {compact_ctx}\nTools: {_tool_schema()}\nReturn JSON array of actions.",
            }
        ],
        default="[]",
    )

    try:
        actions = json.loads(plan) if isinstance(plan, str) else plan
    except Exception:
        actions = []

    return {**state, "actions": actions or []}
