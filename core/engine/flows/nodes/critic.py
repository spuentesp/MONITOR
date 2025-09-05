"""
Critic node for LangGraph flows.

This module contains the critic logic that validates
and provides quality assurance for the generated content.
"""

from typing import Any

from core.engine.flows.agent_utils import safe_agent_call


def critic_node(state: dict[str, Any], tools: Any) -> dict[str, Any]:
    """
    Critic node that validates the generated content.

    Provides quality assurance and validation feedback
    for the draft content and planned actions.
    """

    draft = state.get("draft", "")
    actions = state.get("actions", [])
    continuity = state.get("continuity", {})

    # Build validation context
    validation_context = {
        "draft": draft[:500] if draft else "",  # Truncate for API limits
        "action_count": len(actions),
        "has_continuity_issues": bool(continuity.get("drift") or continuity.get("incorrect")),
        "scene_id": state.get("scene_id"),
        "story_id": state.get("story_id"),
    }

    # Ask critic for validation
    messages = [
        {
            "role": "user",
            "content": f"Validate this content and context: {validation_context}. Return JSON with 'ok' boolean and optional 'warnings' array.",
        }
    ]

    validation_raw = safe_agent_call(tools, "critic", messages, default='{"ok": true, "warnings": []}')

    try:
        import json

        validation = (
            json.loads(validation_raw) if isinstance(validation_raw, str) else validation_raw
        )
        if not isinstance(validation, dict):
            validation = {"ok": True, "warnings": []}
    except Exception:
        validation = {"ok": True, "warnings": ["Failed to parse validation response"]}

    return {**state, "validation": validation}
