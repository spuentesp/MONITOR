"""Flow state management and common utilities."""

from __future__ import annotations

from typing import Any

from core.utils.env import env_bool, env_str


class FlowState(dict):
    """Enhanced state dictionary for LangGraph flows."""

    pass


def env_flag(name: str, default: str = "0") -> bool:
    """Parse common boolean-ish env flags once using shared util."""
    return env_bool(name, default in ("1", "true", "True"))


def safe_act(
    tools: dict[str, Any], agent_key: str, messages: list[dict[str, Any]], default: Any = None
) -> Any:
    """Call tools[agent_key].act(messages) defensively.

    Returns default on error or missing agent.
    """
    try:
        agent = tools.get(agent_key)
        if agent:
            return agent.act(messages)
    except Exception:
        pass
    return default


def fetch_relations(tools: dict[str, Any], scene_id: str) -> list[dict[str, Any]]:
    """Retrieve relations effective in scene via lc_tools (if enabled) or query_tool.

    Returns a list; errors are swallowed to keep flow resilient.
    """
    try:
        lc_tools = tools.get("lc_tools")
        if lc_tools and "query_tool" in lc_tools:
            rels = lc_tools["query_tool"].invoke(
                {"method": "relations_effective_in_scene", "scene_id": scene_id}
            )
        else:
            rels = tools["query_tool"](
                tools["ctx"], "relations_effective_in_scene", scene_id=scene_id
            )
        return rels or []
    except Exception:
        return []


# Environment configuration
MONITOR_VERBOSE_TASKS = env_bool("MONITOR_VERBOSE_TASKS", True)
MONITOR_PERSONA = env_str("MONITOR_PERSONA", "guardian") or "guardian"
