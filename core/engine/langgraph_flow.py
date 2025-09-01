from __future__ import annotations

import os
from typing import Any


def build_langgraph_flow(tools: Any):
    """Build a minimal LangGraph flow using existing tools.

    This function avoids importing langgraph at module import time to keep it optional.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception as e:
        raise RuntimeError("LangGraph is not installed. Please install langgraph.") from e

    # Optional LangChain tools (env-gated)
    lc_tools = None
    if os.getenv("MONITOR_LC_TOOLS", "0") in ("1", "true", "True"):
        try:
            from core.engine.lc_tools import build_langchain_tools

            lc_list = build_langchain_tools(tools["ctx"])  # returns a list of Tool objects
            lc_tools = {t.name: t for t in lc_list}
        except Exception:
            lc_tools = None

    # Simple state for demonstration
    class State(dict):
        pass

    def director(state: dict[str, Any]) -> dict[str, Any]:
        # Use LLM-backed Director if provided; fallback to trivial plan
        intent = state.get("intent", "")
        try:
            if tools.get("director"):
                reply = tools["director"].act([
                    {"role": "user", "content": f"Intent: {intent}. Return a tiny plan."}
                ])
                return {**state, "plan": reply}
        except Exception:
            pass
        return {**state, "plan": {"beats": [intent], "assumptions": []}}

    def librarian(state: dict[str, Any]) -> dict[str, Any]:
        scene_id = state.get("scene_id")
        evidence = []
        if scene_id:
            try:
                if lc_tools and "query_tool" in lc_tools:
                    rels = lc_tools["query_tool"].invoke(
                        {"method": "relations_effective_in_scene", "scene_id": scene_id}
                    )
                else:
                    rels = tools["query_tool"](
                        tools["ctx"], "relations_effective_in_scene", scene_id=scene_id
                    )
                evidence.append({"relations": rels})
            except Exception:
                pass
        # Optionally let LLM librarian summarize evidence
        try:
            if tools.get("librarian") and evidence:
                summary = tools["librarian"].act([
                    {"role": "user", "content": f"Summarize briefly: {str(evidence)[:800]}"}
                ])
                return {**state, "evidence": evidence, "evidence_summary": summary}
        except Exception:
            pass
        return {**state, "evidence": evidence}

    def steward(state: dict[str, Any]) -> dict[str, Any]:
        # LLM-backed steward for quick validation hints
        try:
            if tools.get("steward"):
                hints = tools["steward"].act([
                    {"role": "user", "content": f"Validate plan and draft context: {str({k:v for k,v in state.items() if k in ['plan','evidence']})[:800]}"}
                ])
                return {**state, "validation": {"ok": True, "warnings": [hints]}}
        except Exception:
            pass
        return {**state, "validation": {"ok": True, "warnings": []}}

    def narrator(state: dict[str, Any]) -> dict[str, Any]:
        msgs = [{"role": "user", "content": state.get("intent", "")}]
        draft = tools["narrator"].act(msgs)
        return {**state, "draft": draft}

    def critic(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft", "")
        try:
            if tools.get("critic"):
                critique = tools["critic"].act([{ "role": "user", "content": draft }])
                return {**state, "critique": critique}
        except Exception:
            pass
        return {**state, "critique": {"coherence": 0.9, "length": len(draft)}}

    def archivist(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft", "")
        summary = tools["archivist"].act([{"role": "user", "content": draft}])
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

    # Copilot checkpoint: allow pause before Recorder based on env flag
    def should_pause(_: dict[str, Any]) -> bool:
        # Default: do NOT pause in copilot, so tests reach the recorder node unless explicitly paused
        return os.getenv("MONITOR_COPILOT_PAUSE", "0") in ("1", "true", "True")

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
    """Return 'langgraph' or 'inmemory' based on env (default: inmemory)."""
    val = os.getenv("MONITOR_ENGINE_BACKEND", "inmemory").lower()
    return "langgraph" if val in ("langgraph", "lg") else "inmemory"
