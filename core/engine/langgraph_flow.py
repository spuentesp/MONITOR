from __future__ import annotations

import os
from typing import Any


def _env_flag(name: str, default: str = "0") -> bool:
    """Parse common boolean-ish env flags once.

    Accepts 1/true/True as truthy; everything else is false.
    """
    return os.getenv(name, default) in ("1", "true", "True")


def build_langgraph_flow(tools: Any, config: dict | None = None):
    """Build a minimal LangGraph flow using existing tools.

    This function avoids importing langgraph at module import time to keep it optional.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception as e:
        raise RuntimeError("LangGraph is not installed. Please install langgraph.") from e

    # Optional LangChain tools (env-gated)
    cfg = config or {}
    lc_tools = None
    use_lc_tools = bool(cfg.get("use_lc_tools", _env_flag("MONITOR_LC_TOOLS", "0")))
    if use_lc_tools:
        try:
            from core.engine.lc_tools import build_langchain_tools

            lc_list = build_langchain_tools(tools["ctx"])  # returns a list of Tool objects
            lc_tools = {t.name: t for t in lc_list}
        except Exception:
            lc_tools = None

    # Simple state for demonstration
    class State(dict):
        pass

    def _safe_act(agent_key: str, messages: list[dict[str, Any]], default: Any = None) -> Any:
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

    def _fetch_relations(scene_id: str) -> list[dict[str, Any]]:
        """Retrieve relations effective in scene via lc_tools (if enabled) or query_tool.

        Returns a list; errors are swallowed to keep flow resilient.
        """
        try:
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

    def director(state: dict[str, Any]) -> dict[str, Any]:
        # Use LLM-backed Director if provided; fallback to trivial plan
        intent = state.get("intent", "")
        reply = _safe_act(
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
            return {**state, "plan": structured}
        return {**state, "plan": {"beats": [intent], "assumptions": []}}

    def librarian(state: dict[str, Any]) -> dict[str, Any]:
        scene_id = state.get("scene_id")
        evidence = []
        if scene_id:
            rels = _fetch_relations(scene_id)
            if rels is not None:
                evidence.append({"relations": rels})
        # Optionally let LLM librarian summarize evidence
        if evidence:
            summary = _safe_act(
                "librarian",
                [{"role": "user", "content": f"Summarize briefly: {str(evidence)[:800]}"}],
                default=None,
            )
            if summary is not None:
                return {**state, "evidence": evidence, "evidence_summary": summary}
        return {**state, "evidence": evidence}

    def steward(state: dict[str, Any]) -> dict[str, Any]:
        # LLM-backed steward for quick validation hints
        hints = _safe_act(
            "steward",
            [{
                "role": "user",
                "content": (
                    f"Validate plan and draft context: "
                    f"{str({k: v for k, v in state.items() if k in ['plan', 'evidence']})[:800]}"
                ),
            }],
            default=None,
        )
        if hints is not None:
            return {**state, "validation": {"ok": True, "warnings": [hints]}}
        return {**state, "validation": {"ok": True, "warnings": []}}

    def narrator(state: dict[str, Any]) -> dict[str, Any]:
        msgs = [{"role": "user", "content": state.get("intent", "")}]
        draft = _safe_act("narrator", msgs, default="")
        return {**state, "draft": draft}

    def critic(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft", "")
        critique = _safe_act("critic", [{"role": "user", "content": draft}], default=None)
        if critique is not None:
            return {**state, "critique": critique}
        return {**state, "critique": {"coherence": 0.9, "length": len(draft)}}

    def archivist(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft", "")
        summary = _safe_act("archivist", [{"role": "user", "content": draft}], default="")
        return {**state, "summary": summary}

    def recorder(state: dict[str, Any]) -> dict[str, Any]:
        commit = tools["recorder_tool"](
            tools["ctx"], draft=state.get("draft", ""), deltas={"scene_id": state.get("scene_id")}
        )
        return {**state, "commit": commit}

    workflow = StateGraph(State)
    workflow.add_node("director", director)
    workflow.add_node("librarian", librarian)
    workflow.add_node("steward", steward)
    workflow.add_node("narrator", narrator)
    workflow.add_node("critic", critic)
    workflow.add_node("archivist", archivist)
    workflow.add_node("recorder", recorder)

    workflow.set_entry_point("director")
    workflow.add_edge("director", "librarian")
    workflow.add_edge("librarian", "steward")
    workflow.add_edge("steward", "narrator")
    workflow.add_edge("narrator", "critic")
    workflow.add_edge("critic", "archivist")

    # Copilot checkpoint: allow pause before Recorder based on config/env flag
    pause_before_recorder = bool(
        cfg.get("pause_before_recorder", _env_flag("MONITOR_COPILOT_PAUSE", "0"))
    )

    def should_pause(_: dict[str, Any]) -> bool:
        # Default: do NOT pause in copilot, so tests reach the recorder node unless explicitly paused
        return pause_before_recorder

    workflow.add_conditional_edges(
        "archivist",
        should_pause,
        {True: END, False: "recorder"},
    )
    workflow.add_edge("recorder", END)

    compiled = workflow.compile()

    class FlowAdapter:
        def __init__(self, compiled_graph):
            self._compiled = compiled_graph

        def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
            try:
                out = self._compiled.invoke(inputs)
                if out is not None:
                    return out
            except Exception:
                pass
            # Fallback: sequential execution to produce a final state dict
            state = dict(inputs)
            for fn in (director, librarian, steward, narrator, critic, archivist):
                state = fn(state)
            if not should_pause(state):
                state = recorder(state)
            return state

    return FlowAdapter(compiled)


def select_engine_backend() -> str:
    """Return 'langgraph' by default; allow explicit override via env."""
    val = os.getenv("MONITOR_ENGINE_BACKEND", "langgraph").lower()
    return "langgraph" if val in ("langgraph", "lg") else "inmemory"
