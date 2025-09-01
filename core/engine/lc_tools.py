from __future__ import annotations

from typing import Any


def build_langchain_tools(ctx: Any) -> list[Any]:
    """Return LangChain Tool objects wrapping query, rules, and recorder tools.

    Lazy-imports langchain to keep it optional.
    """
    try:
        from langchain_core.tools import Tool
    except Exception as e:
        raise RuntimeError("LangChain is not installed. Please install langchain.") from e

    def _query(method: str, **kwargs):
        allowed = {
            "system_usage_summary",
            "effective_system_for_universe",
            "effective_system_for_story",
            "effective_system_for_scene",
            "effective_system_for_entity",
            "effective_system_for_entity_in_story",
            "relation_state_history",
            "relations_effective_in_scene",
            "relation_is_active_in_scene",
            # Additional safe read helpers
            "entities_in_scene",
            "facts_for_scene",
        }
        if method not in allowed:
            raise ValueError(f"Query method not allowed: {method}")
        fn = getattr(ctx.query_service, method)
        return fn(**kwargs)

    def _rules(action: str, **kwargs) -> dict[str, Any]:
        return {
            "action": action,
            "inputs": kwargs,
            "result": "partial",
            "effects": [],
            "trace": ["lc:rules_tool"],
        }

    def _recorder(draft: str, **deltas) -> dict[str, Any]:
        # Call our recorder_tool to ensure cache invalidation and staging semantics
        try:
            from core.engine.tools import recorder_tool as _rt

            res = _rt(ctx, draft=draft, deltas=deltas)
        except Exception as e:
            res = {"ok": False, "error": str(e)}
        return res

    return [
        Tool.from_function(
            name="query_tool",
            description="Graph query tool: method=<allowed method>, kwargs serialized as JSON-like arguments.",
            func=_query,
        ),
        Tool.from_function(
            name="rules_tool",
            description="Rules interpreter tool: action=<rule action>, kwargs for parameters.",
            func=_rules,
        ),
        Tool.from_function(
            name="recorder_tool",
            description="Recorder tool: draft text and deltas (scene_id, facts, relations). Dry-run by default.",
            func=_recorder,
        ),
    ]
