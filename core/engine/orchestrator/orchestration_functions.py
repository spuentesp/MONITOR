"""Core orchestration functions for running the narrative engine."""

from __future__ import annotations

import re
from typing import Any

from core.engine.langgraph_flow import select_engine_backend
from core.engine.tools import (
    ToolContext,
    bootstrap_story_tool,
    indexing_tool,
    narrative_tool,
    object_upload_tool,
    query_tool,
    recorder_tool,
    retrieval_tool,
)
from .autocommit_manager import autocommit_stats
from .tool_builder import build_live_tools


def run_once(
    user_intent: str,
    scene_id: str | None = None,
    mode: str = "copilot",
    *,
    ctx: ToolContext | None = None,
    llm: Any | None = None,
) -> dict[str, Any]:
    """Convenience function to run a single step against the live graph.

    Chooses backend by env MONITOR_ENGINE_BACKEND=(inmemory|langgraph); defaults to langgraph.
    In copilot, Recorder can pause if MONITOR_COPILOT_PAUSE is truthy.
    """
    tools = ctx or build_live_tools(dry_run=(mode != "autopilot"))
    from core.generation.providers import select_llm_from_env

    llm = llm or select_llm_from_env()
    backend = select_engine_backend()
    if backend == "langgraph":
        try:
            from core.engine.langgraph_flow import build_langgraph_flow
            from core.agents.factory import build_agents
        except Exception as e:
            # Treat missing/failed LangGraph as app down
            raise RuntimeError(
                "Engine backend unavailable (LangGraph required). App is down."
            ) from e
        tools_pkg = {
            "ctx": tools,
            "query_tool": query_tool,
            "recorder_tool": recorder_tool,
            "bootstrap_story_tool": bootstrap_story_tool,
            "narrative_tool": narrative_tool,
            "indexing_tool": indexing_tool,
            "retrieval_tool": retrieval_tool,
            "object_upload_tool": object_upload_tool,
            "llm": llm,
            **build_agents(llm),
        }
        graph = build_langgraph_flow(tools_pkg)
        out = graph.invoke({"intent": user_intent, "scene_id": scene_id})
        return out
    # If we are not using LangGraph, treat the app as down (no fallback)
    raise RuntimeError("Engine backend unavailable (LangGraph required). App is down.")


def monitor_reply(
    ctx: ToolContext,
    text: str,
    *,
    mode: str | None = None,
    scene_id: str | None = None,
) -> dict[str, Any]:
    """Terse, non-diegetic replies for monitor-prefixed commands.

    Supported intents (minimal PR1 scope):
    - ping: "are you there" → status line(s)
    - audit/inconsistencies/relations → stub audit banner and next steps
    """
    t = (text or "").lower()
    # Status snapshot
    pend = None
    try:
        if getattr(ctx, "staging", None) is not None:
            pend = ctx.staging.pending()
    except Exception:
        pend = None
    try:
        ac = autocommit_stats()
    except Exception:
        ac = {"enabled": False}
    online = True
    status = {
        "online": online,
        "mode": mode or ("autopilot" if not getattr(ctx, "dry_run", True) else "copilot"),
        "staging_pending": pend,
        "autocommit": ac,
        "scene_id": scene_id,
    }

    # Ping
    if re.search(r"are you there|status|online", t):
        lines = [
            "System online.",
            f"Mode: {status['mode']}",
            f"Staging pending: {status['staging_pending']}",
            f"Auto-commit: {'on' if status['autocommit'].get('enabled') else 'off'}",
        ]
        return {"draft": "\n".join(lines), "monitor": True, "details": status}

    # Relations audit (stub)
    if re.search(r"audit|inconsisten|relation", t):
        advice = []
        if not scene_id:
            advice.append("Provide a scene_id to scope the audit (optional but recommended).")
        advice.extend(
            [
                "Check: participants_by_role_for_scene, relations_effective_in_scene.",
                "Flag: mutually exclusive kinship (father vs brother), asymmetric edges, cycles.",
                "Next: propose END/CHANGE relation in current or next scene.",
            ]
        )
        return {
            "draft": "Audit stub: relation checks queued. Provide entity names/ids or a scene_id.",
            "monitor": True,
            "details": {**status, "advice": advice},
        }

    # Fallback: minimal help
    return {
        "draft": "Monitor ready. Say: 'monitor are you there', 'monitor audit relations', 'monitor last story'.",
        "monitor": True,
        "details": status,
    }
