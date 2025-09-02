from __future__ import annotations

import os
from typing import Any
import json


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

    def intent_router(state: dict[str, Any]) -> dict[str, Any]:
        # Let LLM route the input; fallback to narrative
        intent = state.get("intent", "")
        routed = _safe_act("intent_router", [{"role": "user", "content": intent}], default="narrative")
        label = (routed or "narrative").strip().lower()
        return {**state, "intent_type": label}

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

    def planner(state: dict[str, Any]) -> dict[str, Any]:
        """Ask the planner for actions when bootstrap or monitor/audit or action_* intents.

        The planner returns a JSON list of actions, else we keep actions empty.
        """
        intent_type = state.get("intent_type")
        if intent_type in {"bootstrap", "audit_relations", "action_examine", "action_move"}:
            plan = _safe_act(
                "planner",
                [{"role": "user", "content": f"Intent: {state.get('intent')}\nContext: {str({k:v for k,v in state.items() if k in ['scene_id']})}"}],
                default="[]",
            )
            try:
                actions = json.loads(plan) if isinstance(plan, str) else plan
            except Exception:
                actions = []
            return {**state, "actions": actions or []}
        return {**state, "actions": []}

    def execute_actions(state: dict[str, Any]) -> dict[str, Any]:
        actions = state.get("actions") or []
        ctx = tools["ctx"]
        results: list[dict[str, Any]] = []
        new_scene_id = None
        for act in actions:
            try:
                tool = (act or {}).get("tool")
                args = (act or {}).get("args") or {}
                if tool == "bootstrap_story":
                    res = tools["bootstrap_story_tool"](ctx, **args)
                    try:
                        new_scene_id = (
                            (res.get("refs") or {}).get("scene_id")
                            or (res.get("result") or {}).get("scene_id")
                            or new_scene_id
                        )
                    except Exception:
                        pass
                elif tool == "recorder":
                    res = tools["recorder_tool"](ctx, draft="", deltas=args)
                elif tool == "query":
                    res = tools["query_tool"](ctx, **args)
                else:
                    res = {"ok": False, "error": f"unknown tool: {tool}"}
            except Exception as e:
                res = {"ok": False, "error": str(e)}
            results.append({"tool": act.get("tool"), "result": res})
        # If we created a scene, persist it in state for continuity
        next_state = {**state, "action_results": results}
        if new_scene_id and not next_state.get("scene_id"):
            next_state["scene_id"] = new_scene_id
        return next_state

    def qa_node(state: dict[str, Any]) -> dict[str, Any]:
        """Answer classification questions tersely via QA agent and finish."""
        msgs = [{"role": "user", "content": state.get("intent", "")}]
        answer = _safe_act("qa", msgs, default="Unsure — insufficient evidence.")
        return {**state, "qa": answer, "draft": answer}

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
        # Always record a compact Fact per turn to retain memory of choices
        deltas = {"scene_id": state.get("scene_id")}
        draft = state.get("draft", "")
        if draft.strip():
            deltas["facts"] = [
                {
                    "description": (draft[:220]),
                    "occurs_in": state.get("scene_id"),
                }
            ]
        commit = tools["recorder_tool"](tools["ctx"], draft=draft, deltas=deltas)
        return {**state, "commit": commit}

    workflow = StateGraph(State)
    workflow.add_node("intent_router", intent_router)
    workflow.add_node("director", director)
    workflow.add_node("librarian", librarian)
    workflow.add_node("steward", steward)
    workflow.add_node("planner", planner)
    workflow.add_node("execute_actions", execute_actions)
    workflow.add_node("qa_node", qa_node)
    workflow.add_node("narrator", narrator)
    workflow.add_node("critic", critic)
    workflow.add_node("archivist", archivist)
    workflow.add_node("recorder", recorder)

    workflow.set_entry_point("intent_router")
    # Branch on intent_type: monitor/qa short-circuit vs narrative path
    def _route(state: dict[str, Any]):
        it = (state.get("intent_type") or "").lower()
        if it in ("monitor", "audit_relations"):
            return "execute_actions"  # actions will call queries/recorder as needed
        if it == "qa":
            return "qa_node"
        return "director"

    workflow.add_conditional_edges(
        "intent_router",
        _route,
        {
            "execute_actions": "execute_actions",
            "qa_node": "qa_node",
            "director": "director",
        },
    )

    workflow.add_edge("director", "librarian")
    workflow.add_edge("librarian", "steward")
    workflow.add_edge("steward", "planner")
    workflow.add_edge("planner", "execute_actions")
    workflow.add_edge("execute_actions", "narrator")
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
    workflow.add_edge("qa_node", END)

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
            for fn in (intent_router, director, librarian, steward, planner, execute_actions, narrator, critic, archivist):
                state = fn(state)
            if not should_pause(state):
                state = recorder(state)
            return state

    return FlowAdapter(compiled)


def select_engine_backend() -> str:
    """Return 'langgraph' by default; allow explicit override via env."""
    val = os.getenv("MONITOR_ENGINE_BACKEND", "langgraph").lower()
    return "langgraph" if val in ("langgraph", "lg") else "inmemory"
