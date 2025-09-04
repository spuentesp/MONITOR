"""Planning and directing nodes."""
from __future__ import annotations

import json
from typing import Any, Dict

from core.engine.flow_utils import ops_prelude as flow_ops_prelude
from ..state import FlowState, safe_act, MONITOR_PERSONA, MONITOR_VERBOSE_TASKS


def ops_prelude(actions: list[dict[str, Any]]) -> str | None:
    """Generate operations prelude for planned actions."""
    return flow_ops_prelude(actions, persona=MONITOR_PERSONA, verbose=MONITOR_VERBOSE_TASKS)


def director(state: FlowState, tools: Dict[str, Any]) -> FlowState:
    """Create a high-level plan using the Director agent."""
    # Use LLM-backed Director if provided; fallback to trivial plan
    intent = state.get("intent", "")
    reply = safe_act(
        tools,
        "director",
        [{"role": "user", "content": f"Intent: {intent}. Return a tiny plan."}],
        default=None,
    )
    
    if reply is not None:
        # Ensure a structured plan for callers/tests even if LLM returns free text
        structured = {"beats": [intent] if intent else [], "assumptions": []}
        if isinstance(reply, str) and reply.strip():
            structured["notes"] = reply.strip()
        elif isinstance(reply, dict):
            # Merge any dict reply but keep required keys
            structured.update(reply)
            structured.setdefault("beats", [intent] if intent else [])
            structured.setdefault("assumptions", [])
        
        # Add a prelude announcing planned operations (best-effort heuristic)
        try:
            actions = structured.get("actions") or []
            prelude = ops_prelude(actions if isinstance(actions, list) else [])
            if prelude:
                return {**state, "plan": structured, "operations_prelude": prelude}
        except Exception:
            pass
        return {**state, "plan": structured}
    
    return {**state, "plan": {"beats": [intent], "assumptions": []}}


def planner(state: FlowState, tools: Dict[str, Any]) -> FlowState:
    """Agentic planner: always request a JSON list of actions; empty list means no-ops.

    The planner decides if/what to do given intent and context.
    """
    from core.engine.flow_utils import tool_schema as flow_tool_schema
    
    # Provide richer but compact context: IDs and librarian/evidence summary if available
    compact_ctx = {
        k: state.get(k)
        for k in ("scene_id", "story_id", "universe_id", "tags")
        if state.get(k) is not None
    }
    if state.get("evidence_summary"):
        compact_ctx["evidence_summary"] = state.get("evidence_summary")
    
    tool_schema = flow_tool_schema()
    plan = safe_act(
        tools,
        "planner",
        [
            {
                "role": "user",
                "content": f"Intent: {state.get('intent')}\nContext: {compact_ctx}\nTools: {tool_schema}\nReturn JSON array of actions.",
            }
        ],
        default="[]",
    )
    
    try:
        actions = json.loads(plan) if isinstance(plan, str) else plan
    except Exception:
        actions = []
    
    return {**state, "actions": actions or []}
