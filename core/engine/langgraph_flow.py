from __future__ import annotations

from typing import Any, Dict


import os


def build_langgraph_flow(tools: Any):
    """Build a minimal LangGraph flow using existing tools.

    This function avoids importing langgraph at module import time to keep it optional.
    """
    try:
        from langgraph.graph import StateGraph, END
    except Exception as e:
        raise RuntimeError("LangGraph is not installed. Please install langgraph.") from e

    # Simple state for demonstration
    class State(dict):
        pass

    def director(state: Dict[str, Any]) -> Dict[str, Any]:
        intent = state.get("intent", "")
        return {"plan": {"beats": [intent], "assumptions": []}}

    def librarian(state: Dict[str, Any]) -> Dict[str, Any]:
        scene_id = state.get("scene_id")
        evidence = []
        if scene_id:
            try:
                rels = tools["query_tool"](tools["ctx"], "relations_effective_in_scene", scene_id=scene_id)
                evidence.append({"relations": rels})
            except Exception:
                pass
        return {"evidence": evidence}

    def steward(state: Dict[str, Any]) -> Dict[str, Any]:
        return {"validation": {"ok": True, "warnings": []}}

    def narrator(state: Dict[str, Any]) -> Dict[str, Any]:
        llm = tools["llm"]
        msgs = [{"role": "user", "content": state.get("intent", "") }]
        draft = tools["narrator"].act(msgs)
        return {"draft": draft}

    def critic(state: Dict[str, Any]) -> Dict[str, Any]:
        draft = state.get("draft", "")
        return {"critique": {"coherence": 0.9, "length": len(draft)}}

    def archivist(state: Dict[str, Any]) -> Dict[str, Any]:
        draft = state.get("draft", "")
        summary = tools["archivist"].act([{"role": "user", "content": draft}])
        return {"summary": summary}

    def recorder(state: Dict[str, Any]) -> Dict[str, Any]:
        commit = tools["recorder_tool"](tools["ctx"], draft=state.get("draft", ""), deltas={"scene_id": state.get("scene_id")})
        return {"commit": commit}

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
    def should_pause(_: Dict[str, Any]) -> bool:
        return os.getenv("MONITOR_COPILOT_PAUSE", "1") in ("1", "true", "True")

    workflow.add_conditional_edges(
        "archivist",
        should_pause,
        {True: END, False: "recorder"},
    )
    workflow.add_edge("recorder", END)

    return workflow.compile()


def select_engine_backend() -> str:
    """Return 'langgraph' or 'inmemory' based on env (default: inmemory)."""
    val = os.getenv("MONITOR_ENGINE_BACKEND", "inmemory").lower()
    return "langgraph" if val in ("langgraph", "lg") else "inmemory"
