"""Intent routing and classification node."""

from __future__ import annotations

from typing import Any

from ..state import FlowState, env_flag, safe_act


def intent_router(state: FlowState, tools: dict[str, Any]) -> FlowState:
    """Route the input intent using LLM classification."""
    # Let LLM route the input. In strict mode, avoid assuming narrative.
    intent = state.get("intent", "")
    routed = safe_act(tools, "intent_router", [{"role": "user", "content": intent}], default=None)
    label = (routed or "").strip().lower() if isinstance(routed, str) else ""

    if not label and env_flag("MONITOR_AGENTIC_STRICT", "0"):
        label = "qa"  # minimal safe default
    if not label:
        label = "narrative"

    return {**state, "intent_type": label}
